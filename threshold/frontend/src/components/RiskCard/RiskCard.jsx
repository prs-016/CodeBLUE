import { X } from "lucide-react";
import RiskCardSkeleton from "./RiskCardSkeleton";

const RISK_LABELS = { low: "LOW", medium: "MEDIUM", high: "HIGH", critical: "CRITICAL" };
const DISASTER_ICONS = { flood: "🌊", wildfire: "🔥", drought: "☀️", storm: "⛈️", none: "🌍" };

export default function RiskCard({ quick, enrich, loadingQuick, loadingEnrich, onClose }) {
  if (loadingQuick) {
    return (
      <div className="w-80 bg-black/85 border border-grey-dark rounded-2xl backdrop-blur-xl p-5 shadow-2xl">
        <div className="animate-pulse space-y-3">
          <div className="h-4 bg-grey-dark/50 rounded w-1/2" />
          <div className="h-6 bg-grey-dark/50 rounded w-2/3" />
          <div className="h-10 bg-grey-dark/50 rounded w-1/3 mt-2" />
          <div className="h-px bg-grey-dark/40 my-3" />
          <div className="h-4 bg-grey-dark/50 rounded w-full" />
          <div className="h-4 bg-grey-dark/50 rounded w-4/5" />
          <div className="h-4 bg-grey-dark/50 rounded w-3/4" />
        </div>
      </div>
    );
  }

  if (!quick) return null;

  const { region_name, country, weather, disaster } = quick;
  const riskColor = disaster.pin_color;
  const icon = DISASTER_ICONS[disaster.disaster_type] || "🌍";

  return (
    <div
      className="w-80 bg-black/90 border rounded-2xl backdrop-blur-xl p-5 shadow-[0_32px_80px_rgba(0,0,0,0.6)]"
      style={{ borderColor: riskColor + "55", boxShadow: `0 32px 80px rgba(0,0,0,0.6), 0 0 0 1px ${riskColor}22` }}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div>
          <div className="text-xs text-grey-mid uppercase tracking-widest mb-1">{country}</div>
          <h2 className="text-white font-bold text-lg leading-tight">{region_name}</h2>
        </div>
        <button onClick={onClose} className="text-grey-mid hover:text-white transition-colors ml-2 mt-1">
          <X size={16} />
        </button>
      </div>

      {/* Risk badge */}
      <div
        className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg mb-4 text-sm font-bold uppercase tracking-wider"
        style={{ backgroundColor: riskColor + "22", color: riskColor, border: `1px solid ${riskColor}44` }}
      >
        <span>{icon}</span>
        <span>{disaster.disaster_type === "none" ? "No Active Disaster" : disaster.disaster_type}</span>
        <span className="text-xs opacity-70">— {RISK_LABELS[disaster.risk_level]}</span>
      </div>

      {/* Weather stats */}
      <div className="grid grid-cols-2 gap-2 mb-4 text-xs">
        <Stat label="Rainfall 48h" value={weather.rainfall_mm_last_48h !== undefined && weather.rainfall_mm_last_48h !== null ? `${weather.rainfall_mm_last_48h} mm` : "—"} />
        <Stat label="Soil Moisture" value={weather.soil_moisture_pct !== undefined && weather.soil_moisture_pct !== null ? `${(weather.soil_moisture_pct * 100).toFixed(0)}%` : "—"} />
        <Stat label="Wind Gust" value={weather.wind_speed_gust_ms !== undefined && weather.wind_speed_gust_ms !== null ? `${(weather.wind_speed_gust_ms * 3.6).toFixed(0)} km/h` : "—"} />
        <Stat label="Temperature" value={weather.temperature_c !== undefined && weather.temperature_c !== null ? `${weather.temperature_c}°C` : "—"} />
      </div>

      {/* Trigger factors */}
      {disaster.trigger_factors.length > 0 && (
        <div className="mb-4">
          <div className="text-xs text-grey-mid uppercase tracking-wider mb-1">Trigger Factors</div>
          <ul className="space-y-0.5">
            {disaster.trigger_factors.map((f, i) => (
              <li key={i} className="text-xs text-white flex items-center gap-1.5">
                <span style={{ color: riskColor }}>▸</span> {f}
              </li>
            ))}
          </ul>
        </div>
      )}

      <hr className="border-grey-dark mb-4" />

      {/* Headlines */}
      <div className="mb-4">
        <div className="text-xs text-grey-mid uppercase tracking-wider mb-2">Recent Headlines</div>
        {loadingEnrich ? (
          <RiskCardSkeleton />
        ) : enrich?.headlines?.length > 0 ? (
          <ul className="space-y-2">
            {enrich.headlines.slice(0, 4).map((h, i) => (
              <li key={i}>
                <a
                  href={h.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-teal-light hover:text-white transition-colors leading-tight block"
                >
                  {h.title}
                </a>
                <span className="text-xs text-grey-mid">{h.source}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-xs text-grey-mid italic">
            {enrich?.errors?.news ? "Headlines unavailable" : "No recent coverage found"}
          </p>
        )}
      </div>

      {/* Charities */}
      <div>
        <div className="text-xs text-grey-mid uppercase tracking-wider mb-2">Donate</div>
        {loadingEnrich ? (
          <RiskCardSkeleton />
        ) : enrich?.charities?.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {enrich.charities.slice(0, 6).map((c, i) => (
              <a
                key={i}
                href={c.url || "#"}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs px-2 py-1 rounded border border-teal/40 text-teal-light hover:bg-teal/10 transition-colors truncate max-w-[130px]"
                title={c.name}
              >
                {c.name}
              </a>
            ))}
          </div>
        ) : (
          <p className="text-xs text-grey-mid italic">
            {enrich?.errors?.charities ? "Charity lookup failed" : "No organizations found"}
          </p>
        )}
      </div>
    </div>
  );
}

function Stat({ label, value }) {
  return (
    <div className="bg-grey-dark/30 rounded px-2 py-1.5">
      <div className="text-grey-mid text-xs">{label}</div>
      <div className="text-white font-mono text-sm">{value}</div>
    </div>
  );
}
