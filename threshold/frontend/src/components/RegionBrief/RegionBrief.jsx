import React from "react";
import { AlertTriangle, Clock3, Radar } from "lucide-react";
import useRegionBrief from "../../hooks/useRegionBrief";

import BranchingPaths from "./BranchingPaths";
import FundingIntelligence from "./FundingIntelligence";
import NewsFeed from "./NewsFeed";
import StressSignalDashboard from "./StressSignalDashboard";
import ThresholdScoreBreakdown from "./ThresholdScoreBreakdown";

export default function RegionBrief({
  regionId,
  data,
  signals,
  news,
  estimate,
  charities,
  breakdown,
  loading: loadingOverride,
}) {
  const brief = useRegionBrief(regionId);
  const region = data ?? brief.region;
  const regionSignals = signals ?? brief.signals;
  const regionNews = news ?? brief.news;
  const regionEstimate = estimate ?? brief.estimate;
  const scoreBreakdown = breakdown ?? brief.scoreBreakdown;
  const partnerCharities = charities ?? brief.charities ?? [];
  const loading = loadingOverride ?? brief.loading;
  const score = Number(region?.current_score ?? region?.threshold_proximity_score ?? 0);

  if (!region) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="text-center">
          <div className="mx-auto h-12 w-12 animate-spin rounded-full border-4 border-teal/30 border-t-teal-light" />
          <p className="mt-4 text-sm uppercase tracking-[0.25em] text-grey-mid">
            {loading ? "Syncing intelligence feed…" : "Region not found"}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto flex w-full max-w-7xl flex-col gap-6 p-6">
      <section className="rounded-[32px] border border-grey-dark/80 bg-[radial-gradient(circle_at_top_left,rgba(230,126,34,0.16),transparent_28%),linear-gradient(160deg,rgba(10,22,40,0.98),rgba(14,28,51,0.95))] p-7 shadow-[0_24px_80px_rgba(0,0,0,0.45)]">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="text-xs uppercase tracking-[0.32em] text-grey-mid">Region intelligence brief</div>
            <h2 className="mt-3 text-4xl font-semibold text-white">{region.name}</h2>
            <p className="mt-2 max-w-2xl text-sm text-grey-mid">{region.primary_driver}</p>
          </div>
          <div className="rounded-[24px] border border-white/10 bg-black/20 px-5 py-4 text-right">
            <div className="text-xs uppercase tracking-[0.2em] text-grey-mid">{loading ? "Syncing" : brief.source}</div>
            <div className="mt-1 font-mono text-4xl text-white">{score.toFixed(1)}</div>
          </div>
        </div>

        <div className="mt-6 grid gap-4 md:grid-cols-3">
          <div className="rounded-[24px] border border-grey-dark/70 bg-black/20 p-4">
            <div className="flex items-center gap-2 text-xs uppercase tracking-[0.2em] text-grey-mid">
              <Clock3 className="h-4 w-4 text-orange" />
              Days to threshold
            </div>
            <div className="mt-2 font-mono text-3xl text-white">{region.days_to_threshold}</div>
          </div>
          <div className="rounded-[24px] border border-grey-dark/70 bg-black/20 p-4">
            <div className="flex items-center gap-2 text-xs uppercase tracking-[0.2em] text-grey-mid">
              <AlertTriangle className="h-4 w-4 text-red-alert" />
              Alert level
            </div>
            <div className="mt-2 font-mono text-3xl text-white">{region.alert_level ?? region.bleaching_alert_level ?? 0}/4</div>
          </div>
          <div className="rounded-[24px] border border-grey-dark/70 bg-black/20 p-4">
            <div className="flex items-center gap-2 text-xs uppercase tracking-[0.2em] text-grey-mid">
              <Radar className="h-4 w-4 text-teal-light" />
              Primary threat
            </div>
            <div className="mt-2 text-2xl font-medium capitalize text-white">{region.primary_threat}</div>
          </div>
        </div>
      </section>

      <ThresholdScoreBreakdown score={score} primaryDriver={region.primary_driver} breakdown={scoreBreakdown} />
      <StressSignalDashboard signals={regionSignals} regionName={region.name} />

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
        <FundingIntelligence region={region} estimate={regionEstimate} charities={partnerCharities} />
        <BranchingPaths estimate={regionEstimate} region={region} />
      </div>

      <NewsFeed items={regionNews} />
    </div>
  );
}
