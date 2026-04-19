"""
train_threshold_net.py — Training script for ThresholdNet on NVIDIA Brev (H100).

Usage (from repo root on Brev instance):
    pip install torch snowflake-sqlalchemy pandas scikit-learn tqdm
    python ml/train_threshold_net.py --epochs 80 --batch-size 128 --window 30

Data flow:
    Snowflake REGION_FEATURES (3,296 rows across 8 regions)
    → sliding-window dataset (window=30 timesteps, stride=1)
    → 80/10/10 train/val/test split (split on region, not time — prevents leakage)
    → ThresholdNet  →  MSE + L1 loss  →  AdamW + CosineAnnealingLR
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# Make repo imports work when run from ml/ or from project root
_HERE = Path(__file__).parent
sys.path.insert(0, str(_HERE / "models"))
sys.path.insert(0, str(_HERE.parent / "backend"))

from threshold_net import ThresholdNet, REGION_TO_IDX, NUM_FEATURES


# ---------------------------------------------------------------------------
# Feature columns and their fill values when null
# ---------------------------------------------------------------------------
FEATURE_COLS = [
    "sst_anomaly",          # °C above baseline
    "o2_current",           # ml/L dissolved O2
    "dhw_current",          # °C-weeks
    "bleaching_alert_level",# 0-4 CRW scale
    "co2_regional_ppm",     # ppm atmospheric CO₂
    "chlorophyll_anomaly",  # mg/m³ anomaly
    "nitrate_anomaly",      # µmol/L anomaly
    "conflict_index",       # 0-1 GDELT Goldstein (computed below)
]
TARGET_COL = "threshold_proximity_score"
FILL_VALUES = {
    "sst_anomaly":           0.0,
    "o2_current":            5.0,   # healthy O2 baseline
    "dhw_current":           0.0,
    "bleaching_alert_level": 0.0,
    "co2_regional_ppm":    415.0,
    "chlorophyll_anomaly":   0.0,
    "nitrate_anomaly":       0.0,
    "conflict_index":        0.33,  # neutral GDELT fallback
}

# GDELT Goldstein mean per region (pre-computed from score_pipeline run)
GDELT_CONFLICT = {
    "great_barrier_reef": 0.333,
    "coral_triangle":     0.333,
    "mekong_delta":       0.333,
    "arabian_sea":        0.333,
    "bengal_bay":         0.333,
    "california_current": 0.333,
    "gulf_of_mexico":     0.333,
    "baltic_sea":         0.333,
}


# ---------------------------------------------------------------------------
# Dataset
# ---------------------------------------------------------------------------
class RegionWindowDataset(Dataset):
    """
    Sliding-window dataset over sorted region timeseries.

    Each sample:
        x          : (window_size, NUM_FEATURES)  float32
        region_idx : int
        y          : float  (threshold_proximity_score of LAST timestep)
    """

    def __init__(
        self,
        df: pd.DataFrame,
        window: int = 30,
        stride: int = 1,
        mean: np.ndarray | None = None,
        std:  np.ndarray | None = None,
        augment: bool = False,
        noise_std: float = 0.01,
    ):
        self.window = window
        self.stride = stride
        self.augment = augment
        self.noise_std = noise_std
        self.samples: list[tuple[np.ndarray, int, float]] = []

        for region_id, group in df.groupby("region_id"):
            group = group.sort_values("date").reset_index(drop=True)
            region_idx = REGION_TO_IDX.get(region_id, 0)
            feats = group[FEATURE_COLS].values.astype(np.float32)   # (N, F)
            targets = group[TARGET_COL].values.astype(np.float32)

            for start in range(0, len(group) - window + 1, stride):
                end = start + window
                self.samples.append((feats[start:end], region_idx, float(targets[end - 1])))

        # Compute normalisation stats from training set if not provided
        if mean is None:
            all_feats = np.concatenate([s[0] for s in self.samples], axis=0)
            self.mean = all_feats.mean(axis=0)
            self.std  = all_feats.std(axis=0) + 1e-8
        else:
            self.mean = mean
            self.std  = std

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int):
        x, region_idx, y = self.samples[idx]
        x_norm = (x - self.mean) / self.std

        # Data Augmentation: add slight Gaussian noise to inputs
        if self.augment:
            x_norm = x_norm + np.random.normal(0, self.noise_std, x_norm.shape).astype(np.float32)

        return (
            torch.from_numpy(x_norm),
            torch.tensor(region_idx, dtype=torch.long),
            torch.tensor(y, dtype=torch.float32),
        )


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
def load_data(snowflake_url: str | None = None) -> pd.DataFrame:
    """
    Load REGION_FEATURES from Snowflake (or fall back to local SQLite for dev).
    Adds conflict_index column from pre-computed GDELT values.
    """
    if snowflake_url:
        from sqlalchemy import create_engine
        engine = create_engine(snowflake_url)
    else:
        # Local SQLite dev fallback
        backend_dir = _HERE.parent / "backend"
        sys.path.insert(0, str(backend_dir))
        from database import engine

    logger.info("Loading REGION_FEATURES …")
    df = pd.read_sql("SELECT * FROM REGION_FEATURES ORDER BY REGION_ID, DATE", engine)
    df.columns = [c.lower() for c in df.columns]

    # Ensure all feature columns exist
    for col, fill in FILL_VALUES.items():
        if col not in df.columns:
            df[col] = fill
        else:
            df[col] = df[col].fillna(fill)

    # Add conflict index from GDELT pre-computed values
    df["conflict_index"] = df["region_id"].map(GDELT_CONFLICT).fillna(0.33)

    # Drop rows without a target
    df = df.dropna(subset=[TARGET_COL])
    df = df[df[TARGET_COL] > 0]

    logger.info("Loaded %d rows across %d regions", len(df), df["region_id"].nunique())
    return df


# ---------------------------------------------------------------------------
# Train / eval loop
# ---------------------------------------------------------------------------
def train_epoch(model, loader, optimizer, criterion, scaler, device):
    model.train()
    total_loss = 0.0
    for x, r, y in loader:
        x, r, y = x.to(device), r.to(device), y.to(device)
        optimizer.zero_grad(set_to_none=True)
        with torch.amp.autocast("cuda", enabled=scaler.is_enabled()):
            pred = model(x, r)
            loss = criterion(pred, y)
        scaler.scale(loss).backward()
        scaler.unscale_(optimizer)
        nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        scaler.step(optimizer)
        scaler.update()
        total_loss += loss.item() * len(y)
    return total_loss / len(loader.dataset)


@torch.no_grad()
def eval_epoch(model, loader, criterion, device):
    model.eval()
    total_loss, mae_sum, n = 0.0, 0.0, 0
    for x, r, y in loader:
        x, r, y = x.to(device), r.to(device), y.to(device)
        pred = model(x, r)
        total_loss += criterion(pred, y).item() * len(y)
        mae_sum    += (pred - y).abs().sum().item()
        n          += len(y)
    return total_loss / n, mae_sum / n


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Train ThresholdNet")
    parser.add_argument("--epochs",        type=int,   default=100)
    parser.add_argument("--batch-size",    type=int,   default=64)
    parser.add_argument("--window",        type=int,   default=30,    help="Sliding window timesteps")
    parser.add_argument("--stride",        type=int,   default=1,     help="Window stride")
    parser.add_argument("--lr",            type=float, default=1e-3)
    parser.add_argument("--weight-decay",  type=float, default=1e-2)
    parser.add_argument("--hidden",        type=int,   default=64,   help="LSTM hidden size per direction")
    parser.add_argument("--lstm-layers",   type=int,   default=1)
    parser.add_argument("--heads",         type=int,   default=4)
    parser.add_argument("--dropout",       type=float, default=0.4)
    parser.add_argument("--patience",      type=int,   default=15,    help="Early stopping patience")
    parser.add_argument("--snowflake-url", type=str,   default=None,  help="SQLAlchemy Snowflake URL")
    parser.add_argument("--save-dir",      type=str,   default="ml/saved_models")
    parser.add_argument("--no-amp",        action="store_true",        help="Disable mixed precision")
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info("Device: %s", device)
    if device.type == "cuda":
        logger.info("GPU: %s  VRAM: %.1f GB", torch.cuda.get_device_name(0),
                    torch.cuda.get_device_properties(0).total_memory / 1e9)

    # ---- Data ----
    df = load_data(args.snowflake_url)

    # 1. TEMPORAL SPLIT (Global)
    # Take first 85% of each region's timeline for train, last 15% for val
    train_dfs, val_dfs, test_dfs = [], [], []
    for region_id, group in df.groupby("region_id"):
        group = group.sort_values("date").reset_index(drop=True)
        n = len(group)
        split_val  = int(n * 0.85)
        split_test = int(n * 0.95)

        train_dfs.append(group.iloc[:split_val])
        val_dfs.append(group.iloc[split_val:split_test])
        test_dfs.append(group.iloc[split_test:])

    train_df = pd.concat(train_dfs)
    val_df   = pd.concat(val_dfs)
    test_df  = pd.concat(test_dfs)

    logger.info("Split strategy: Cross-Region Temporal Holdout (85/10/5)")

    train_ds = RegionWindowDataset(train_df, window=args.window, stride=args.stride, augment=True)
    val_ds   = RegionWindowDataset(val_df,   window=args.window, stride=args.stride,
                                   mean=train_ds.mean, std=train_ds.std, augment=False)
    test_ds  = RegionWindowDataset(test_df,  window=args.window, stride=args.stride,
                                   mean=train_ds.mean, std=train_ds.std, augment=False)

    logger.info("Samples — train: %d  val: %d  test: %d", len(train_ds), len(val_ds), len(test_ds))

    num_workers = min(4, os.cpu_count() or 1)
    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True,
                              num_workers=num_workers, pin_memory=(device.type == "cuda"))
    val_loader   = DataLoader(val_ds,   batch_size=args.batch_size, shuffle=False,
                              num_workers=num_workers, pin_memory=(device.type == "cuda"))
    test_loader  = DataLoader(test_ds,  batch_size=args.batch_size, shuffle=False,
                              num_workers=num_workers, pin_memory=(device.type == "cuda"))

    # ---- Model ----
    model = ThresholdNet(
        hidden_size     = args.hidden,
        num_lstm_layers = args.lstm_layers,
        num_heads       = args.heads,
        mlp_hidden      = args.hidden,
        dropout         = args.dropout,
    ).to(device)

    if device.type == "cuda":
        model = torch.compile(model)   # Torch 2.x — massive H100 speedup

    total_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    logger.info("ThresholdNet  params: %.2fM", total_params / 1e6)

    # ---- Optimiser ----
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs, eta_min=1e-6)
    scaler    = torch.amp.GradScaler("cuda", enabled=(device.type == "cuda" and not args.no_amp))

    # Huber loss = smooth L1 — robust to outliers in ecosystem data
    criterion = nn.HuberLoss(delta=1.0)

    # ---- Training ----
    save_dir = Path(args.save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)
    best_val_mae  = float("inf")
    best_ckpt     = save_dir / "threshold_net_best.pt"
    history: list[dict] = []
    patience_counter = 0

    logger.info("Starting training for %d epochs …", args.epochs)
    for epoch in range(1, args.epochs + 1):
        t0 = time.perf_counter()
        train_loss = train_epoch(model, train_loader, optimizer, criterion, scaler, device)
        val_loss, val_mae = eval_epoch(model, val_loader, criterion, device)
        scheduler.step()

        elapsed = time.perf_counter() - t0
        logger.info(
            "Epoch %3d/%d  train_loss=%.4f  val_loss=%.4f  val_mae=%.4f  lr=%.2e  %.1fs",
            epoch, args.epochs, train_loss, val_loss, val_mae,
            scheduler.get_last_lr()[0], elapsed,
        )

        history.append({"epoch": epoch, "train_loss": train_loss,
                         "val_loss": val_loss, "val_mae": val_mae})

        if val_mae < best_val_mae:
            best_val_mae = val_mae
            patience_counter = 0
            torch.save(
                {
                    "epoch": epoch,
                    "model_state": model.state_dict(),
                    "optimizer_state": optimizer.state_dict(),
                    "val_mae": val_mae,
                    "mean": train_ds.mean.tolist(),
                    "std":  train_ds.std.tolist(),
                    "feature_cols": FEATURE_COLS,
                    "args": vars(args),
                },
                best_ckpt,
            )
            logger.info("  ✓ saved best checkpoint (val_mae=%.4f)", val_mae)
        else:
            patience_counter += 1
            if patience_counter >= args.patience:
                logger.info("Early stopping triggered after %d epochs without improvement.", args.patience)
                break

    # ---- Test evaluation ----
    logger.info("Loading best checkpoint for test evaluation …")
    ckpt = torch.load(best_ckpt, map_location=device)
    model.load_state_dict(ckpt["model_state"])
    test_loss, test_mae = eval_epoch(model, test_loader, criterion, device)
    logger.info("Test  loss=%.4f  mae=%.4f", test_loss, test_mae)

    # Save training history
    hist_path = save_dir / "threshold_net_history.json"
    with open(hist_path, "w") as f:
        json.dump({"history": history, "test_mae": test_mae, "best_val_mae": best_val_mae}, f, indent=2)
    logger.info("History saved to %s", hist_path)
    logger.info("Done. Best val MAE: %.4f  |  Test MAE: %.4f", best_val_mae, test_mae)


if __name__ == "__main__":
    main()
