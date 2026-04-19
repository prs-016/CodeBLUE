import { Activity, Database } from "lucide-react";
import React, { useCallback, useEffect, useState } from "react";

import RiskCard from "../components/RiskCard/RiskCard";
import WarRoomGlobe from "../components/Globe/WarRoomGlobe";
import { useRegions } from "../hooks";
import { useRiskAssessment } from "../hooks/useRiskAssessment";

const API_BASE = (typeof import.meta !== "undefined" && import.meta?.env?.VITE_API_URL) || "http://localhost:8000";

const STATUS_DOT = {
  live:          "bg-teal-light animate-pulse",
  grounded:      "bg-teal-light animate-pulse",
  snowflake:     "bg-blue-400 animate-pulse",
  not_configured:"bg-grey-dark",
};

export default function Home() {
  const { regions } = useRegions();
  const { quick, enrich, loadingQuick, loadingEnrich, assess, clear } = useRiskAssessment();
  const [dataSources, setDataSources] = useState(null);

  useEffect(() => {
    fetch(`${API_BASE}/api/v1/admin/data-sources`)
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (d) setDataSources(d); })
      .catch(() => {});
  }, []);

  const critical = [...regions].sort(
    (a, b) => (b.threshold_proximity_score || 0) - (a.threshold_proximity_score || 0)
  )[0];

  const handleAssess = useCallback(
    (lat, lng) => {
      assess(lat, lng);
    },
    [assess]
  );

  const handleClose = useCallback(() => {
    clear();
  }, [clear]);

  const showRiskCard = loadingQuick || quick;

  return (
    <div className="relative h-screen w-full overflow-hidden bg-navy">
      {/* Radial vignette */}
      <div className="pointer-events-none absolute inset-0 z-0 bg-[radial-gradient(ellipse_at_center,rgba(14,28,51,0.2)_0%,rgba(7,14,26,0.85)_100%)]" />

      {/* ── 3D Globe ── */}
      <div className="absolute inset-0 z-10">
        <WarRoomGlobe
          regions={regions}
          onAssess={handleAssess}
        />
      </div>

      {/* ── HUD overlay ── pointer-events-none by default, re-enabled on interactive children */}
      <div className="pointer-events-none absolute inset-0 z-20 flex flex-col">

        {/* Top bar */}
        <div className="flex items-start justify-between p-6 pt-24">
          {/* Top-left: branding */}
          <div>
            <h1 className="font-sans text-3xl font-black tracking-[0.15em] text-teal-light">
              THRESHOLD
            </h1>
            <p className="mt-1 text-xs uppercase tracking-[0.3em] text-grey-mid">
              Climate Crisis Intelligence
            </p>
          </div>

          {/* Top-right: Critical anomaly badge */}
          {critical && (
            <div className="rounded-xl border border-red-alert/40 bg-black/50 px-4 py-3 text-right shadow-[0_0_20px_rgba(192,57,43,0.25)] backdrop-blur-md">
              <div className="mb-1 flex items-center justify-end gap-2">
                <Activity className="h-3.5 w-3.5 animate-pulse text-red-alert" />
                <span className="font-mono text-[10px] font-bold uppercase tracking-widest text-red-alert">
                  Critical Anomaly
                </span>
              </div>
              <p className="text-sm font-semibold text-white">{critical.name}</p>
              <div className="mt-0.5 font-mono text-2xl font-black text-orange">
                T‑{critical.days_to_threshold ?? "—"}
              </div>
              <p className="text-[10px] text-grey-mid">days to threshold</p>
            </div>
          )}
        </div>

        {/* Spacer */}
        <div className="flex-1" />

        {/* Bottom bar: live stats */}
        <div className="flex items-end justify-between p-6 pb-8">
          {/* Bottom-left: live data sources */}
          <div className="rounded-xl border border-grey-dark/60 bg-black/40 px-4 py-3 backdrop-blur-md min-w-[220px]">
            <div className="flex items-center gap-1.5 mb-2">
              <Database className="w-3 h-3 text-teal-light" />
              <span className="text-[10px] uppercase tracking-[0.25em] text-teal-light font-mono">Live Data Feeds</span>
            </div>
            {dataSources ? (
              <div className="space-y-1.5">
                {dataSources.sources.map((src, i) => (
                  <div key={i} className="flex items-center justify-between gap-3">
                    <div className="flex items-center gap-1.5 min-w-0">
                      <div className={`w-1.5 h-1.5 rounded-full shrink-0 ${STATUS_DOT[src.status] || "bg-grey-mid"}`} />
                      <span className="font-mono text-[10px] text-white truncate">{src.name}</span>
                    </div>
                    <span className="font-mono text-[10px] text-grey-mid shrink-0">
                      {src.rows != null ? src.rows.toLocaleString() : src.status}
                    </span>
                  </div>
                ))}
                <div className="mt-2 pt-2 border-t border-grey-dark/50 font-mono text-[9px] text-grey-dark">
                  Snowflake · {dataSources.snowflake_database} · {regions.length} regions
                </div>
              </div>
            ) : (
              <div className="mt-0.5 font-mono text-xl text-white">{regions.length} regions</div>
            )}
          </div>

          {/* Bottom-right: highest score */}
          {critical && (
            <div className="rounded-xl border border-orange/30 bg-black/40 px-4 py-3 text-right backdrop-blur-md">
              <div className="text-[10px] uppercase tracking-[0.25em] text-grey-mid">Peak score</div>
              <div className="mt-0.5 font-mono text-xl text-orange">
                {(critical.threshold_proximity_score || 0).toFixed(1)}
                <span className="ml-1 text-sm text-grey-mid">/10</span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ── Click instruction hint (fades once card appears) ── */}
      {!showRiskCard && (
        <div className="pointer-events-none absolute bottom-20 left-1/2 z-20 -translate-x-1/2">
          <div className="flex items-center gap-2 rounded-full border border-white/10 bg-black/30 px-4 py-2 backdrop-blur-md">
            <div className="h-1.5 w-1.5 animate-ping rounded-full bg-teal-light/60" />
            <span className="text-[11px] uppercase tracking-[0.2em] text-grey-mid">
              Click globe to assess real-time risk
            </span>
          </div>
        </div>
      )}

      {/* ── RiskCard — z-30, left side, clear of top-right HUD ── */}
      {showRiskCard && (
        <div className="pointer-events-auto absolute left-6 top-1/2 z-30 -translate-y-1/2">
          <RiskCard
            quick={quick}
            enrich={enrich}
            loadingQuick={loadingQuick}
            loadingEnrich={loadingEnrich}
            onClose={handleClose}
          />
        </div>
      )}

    </div>
  );
}
