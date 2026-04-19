"""
threshold_net.py — ThresholdNet: BiLSTM + Multi-Head Attention for ecosystem threshold proximity scoring.

Architecture overview
---------------------
Input  : sliding window of T timesteps × 8 features, plus a region embedding
Encoder: 2-layer Bidirectional LSTM  →  captures local temporal dynamics
Attn   : 4-head self-attention over the LSTM sequence  →  long-range dependencies
Pooling: attention-weighted mean  →  fixed-size context vector
Head   : MLP regressor  →  scalar score ∈ [0, 10]

Features (8 channels, all normalised to z-scores during training)
------------------------------------------------------------------
0  sst_anomaly          °C above baseline        IPCC AR6 coral signal
1  o2_current           ml/L dissolved oxygen    EPA hypoxia proxy
2  dhw_current          °C-weeks                 NOAA CRW coral heat stress
3  bleaching_alert_level 0-4 CRW scale
4  co2_regional_ppm     ppm atmospheric CO₂      acidification proxy
5  chlorophyll_anomaly  mg/m³ anomaly             nutrient/eutrophication
6  nitrate_anomaly      µmol/L anomaly
7  conflict_index       0-1 from GDELT Goldstein  political pressure

Region embedding (8 regions → learned 16-dim vector, concatenated to context)
allows the model to capture region-specific baseline differences.

Output: threshold_proximity_score  ∈  [0.0, 10.0]
"""
from __future__ import annotations

import math
from typing import Optional

import torch
import torch.nn as nn
import torch.nn.functional as F


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
NUM_FEATURES = 8       # input feature channels
NUM_REGIONS  = 8       # known ecosystem regions
REGION_EMB   = 16      # embedding dimension per region


REGION_TO_IDX: dict[str, int] = {
    "great_barrier_reef": 0,
    "coral_triangle":     1,
    "mekong_delta":       2,
    "arabian_sea":        3,
    "bengal_bay":         4,
    "california_current": 5,
    "gulf_of_mexico":     6,
    "baltic_sea":         7,
}


# ---------------------------------------------------------------------------
# Multi-Head Self-Attention (manual impl — avoids FlashAttention dependency
# while being drop-in replaceable with nn.MultiheadAttention)
# ---------------------------------------------------------------------------
class MultiHeadSelfAttention(nn.Module):
    def __init__(self, d_model: int, num_heads: int, dropout: float = 0.1):
        super().__init__()
        assert d_model % num_heads == 0
        self.num_heads = num_heads
        self.head_dim  = d_model // num_heads
        self.scale     = math.sqrt(self.head_dim)

        self.qkv  = nn.Linear(d_model, 3 * d_model, bias=False)
        self.proj = nn.Linear(d_model, d_model)
        self.drop = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor, mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        x   : (B, T, d_model)
        mask: (B, T) bool — True positions are IGNORED (padding)
        returns: (B, T, d_model)
        """
        B, T, D = x.shape
        H, Hd   = self.num_heads, self.head_dim

        qkv = self.qkv(x).reshape(B, T, 3, H, Hd).permute(2, 0, 3, 1, 4)
        q, k, v = qkv[0], qkv[1], qkv[2]                    # (B, H, T, Hd)

        attn = (q @ k.transpose(-2, -1)) / self.scale        # (B, H, T, T)
        if mask is not None:
            # mask out padded positions
            attn = attn.masked_fill(mask[:, None, None, :], float("-inf"))
        attn = self.drop(F.softmax(attn, dim=-1))

        out = (attn @ v).transpose(1, 2).reshape(B, T, D)    # (B, T, D)
        return self.proj(out)


# ---------------------------------------------------------------------------
# ThresholdNet
# ---------------------------------------------------------------------------
class ThresholdNet(nn.Module):
    """
    BiLSTM + Multi-Head Attention regressor.

    Parameters
    ----------
    hidden_size   : LSTM hidden units per direction (256 → 512 bidirectional)
    num_lstm_layers: stacked LSTM depth
    num_heads     : attention heads (must divide 2*hidden_size)
    mlp_hidden    : MLP regression head hidden width
    dropout       : applied after LSTM, within attention, and between MLP layers
    """

    def __init__(
        self,
        hidden_size:     int   = 256,
        num_lstm_layers: int   = 2,
        num_heads:       int   = 4,
        mlp_hidden:      int   = 256,
        dropout:         float = 0.2,
    ):
        super().__init__()

        # Feature projection — normalise raw sensor values before LSTM
        self.input_proj = nn.Sequential(
            nn.Linear(NUM_FEATURES, hidden_size),
            nn.LayerNorm(hidden_size),
            nn.GELU(),
        )

        # Region embedding
        self.region_emb = nn.Embedding(NUM_REGIONS + 1, REGION_EMB, padding_idx=NUM_REGIONS)

        # Bidirectional LSTM encoder
        lstm_out = 2 * hidden_size
        self.lstm = nn.LSTM(
            input_size   = hidden_size,
            hidden_size  = hidden_size,
            num_layers   = num_lstm_layers,
            batch_first  = True,
            bidirectional= True,
            dropout      = dropout if num_lstm_layers > 1 else 0.0,
        )
        self.lstm_drop = nn.Dropout(dropout)
        self.lstm_norm = nn.LayerNorm(lstm_out)

        # Self-attention over sequence
        self.attention  = MultiHeadSelfAttention(lstm_out, num_heads, dropout)
        self.attn_norm  = nn.LayerNorm(lstm_out)

        # Learned attention-weighted pooling query
        self.pool_query = nn.Parameter(torch.randn(1, 1, lstm_out) * 0.02)

        # MLP regression head
        context_dim = lstm_out + REGION_EMB
        self.head = nn.Sequential(
            nn.Linear(context_dim, mlp_hidden),
            nn.LayerNorm(mlp_hidden),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(mlp_hidden, mlp_hidden // 2),
            nn.GELU(),
            nn.Dropout(dropout / 2),
            nn.Linear(mlp_hidden // 2, 1),
        )

    # ------------------------------------------------------------------
    def _attention_pool(self, seq: torch.Tensor, mask: Optional[torch.Tensor]) -> torch.Tensor:
        """
        Attend from a learned query over the sequence → (B, D) context.
        mask: (B, T) True = valid timestep
        """
        B, T, D = seq.shape
        q = self.pool_query.expand(B, -1, -1)                # (B, 1, D)
        k = v = seq                                           # (B, T, D)
        attn_w = (q @ k.transpose(-2, -1)) / math.sqrt(D)   # (B, 1, T)
        if mask is not None:
            pad_mask = ~mask                                   # True = padding
            attn_w = attn_w.masked_fill(pad_mask[:, None, :], float("-inf"))
        attn_w = F.softmax(attn_w, dim=-1)
        out = (attn_w @ v).squeeze(1)                         # (B, D)
        return out

    # ------------------------------------------------------------------
    def forward(
        self,
        x:          torch.Tensor,
        region_idx: torch.Tensor,
        mask:       Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """
        Parameters
        ----------
        x          : (B, T, NUM_FEATURES)  — normalised feature windows
        region_idx : (B,)                  — integer region IDs  (use REGION_TO_IDX)
        mask       : (B, T) bool           — True = valid, False = padding  (optional)

        Returns
        -------
        score : (B,) tensor, clamped to [0, 10]
        """
        # 1. Project features
        h = self.input_proj(x)                     # (B, T, hidden)

        # 2. BiLSTM
        if mask is not None:
            lengths = mask.sum(dim=1).cpu()
            packed  = nn.utils.rnn.pack_padded_sequence(
                h, lengths, batch_first=True, enforce_sorted=False
            )
            lstm_out, _ = self.lstm(packed)
            h, _ = nn.utils.rnn.pad_packed_sequence(lstm_out, batch_first=True)
        else:
            h, _ = self.lstm(h)                    # (B, T, 2*hidden)

        h = self.lstm_norm(self.lstm_drop(h))

        # 3. Self-attention over sequence (residual)
        pad_mask = (~mask) if mask is not None else None
        h = self.attn_norm(h + self.attention(h, pad_mask))

        # 4. Attention-weighted pooling → context vector
        ctx = self._attention_pool(h, mask)        # (B, 2*hidden)

        # 5. Concatenate region embedding
        r_emb = self.region_emb(region_idx)        # (B, REGION_EMB)
        ctx   = torch.cat([ctx, r_emb], dim=-1)    # (B, 2*hidden + REGION_EMB)

        # 6. MLP head → scalar
        out = self.head(ctx).squeeze(-1)           # (B,)
        return torch.clamp(out, 0.0, 10.0)


# ---------------------------------------------------------------------------
# Convenience: count parameters
# ---------------------------------------------------------------------------
def count_params(model: nn.Module) -> str:
    n = sum(p.numel() for p in model.parameters() if p.requires_grad)
    return f"{n / 1_000_000:.2f}M" if n >= 1_000_000 else f"{n / 1_000:.1f}K"


if __name__ == "__main__":
    model = ThresholdNet()
    print(f"ThresholdNet parameters: {count_params(model)}")
    # Smoke test
    B, T = 4, 30
    x  = torch.randn(B, T, NUM_FEATURES)
    r  = torch.randint(0, NUM_REGIONS, (B,))
    m  = torch.ones(B, T, dtype=torch.bool)
    out = model(x, r, m)
    print(f"Output shape: {out.shape}  min={out.min():.3f}  max={out.max():.3f}")
