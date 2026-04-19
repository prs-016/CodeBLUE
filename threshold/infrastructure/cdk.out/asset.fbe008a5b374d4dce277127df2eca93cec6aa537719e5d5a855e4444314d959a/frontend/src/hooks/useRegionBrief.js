import { useApiResource } from "./useApiResource";
import { useRegion, useRegionTrajectory } from "./useRegions";

function summarizeDrivers(region) {
  if (region?.breakdown) return region.breakdown;
  
  // Fallback for missing breakdown
  return [
    {
      key: "thermal",
      label: "SST Anomaly",
      value: region?.latest_sst_anomaly ?? 0,
      detail: "Live sensor data · °C above baseline",
    },
    {
      key: "oxygen",
      label: "Dissolved Oxygen",
      value: region?.latest_o2_current ?? 0,
      detail: "Hypoxia monitor · ml/L",
    },
    {
      key: "productivity",
      label: "Chlorophyll",
      value: region?.latest_chlorophyll_anomaly ?? 0,
      detail: "Ecosystem primary production",
    },
    {
      key: "stability",
      label: "Nitrate Anomaly",
      value: region?.latest_nitrate_anomaly ?? 0,
      detail: "Scripps CalCOFI water quality",
    },
  ];
}

export default function useRegionBrief(regionId) {
  const { region, ...regionState } = useRegion(regionId);
  const trajectoryState = useRegionTrajectory(regionId);

  const signalsState = useApiResource({
    endpoint: regionId ? `/api/v1/regions/${regionId}/stress-signals` : null,
    enabled: Boolean(regionId),
    dependencies: [regionId],
  });

  const newsState = useApiResource({
    endpoint: regionId ? `/api/v1/news/${regionId}` : null,
    enabled: Boolean(regionId),
    dependencies: [regionId],
    transform: (rows) =>
      rows.map((item) => {
        const isIntel = item.source_type === 'gemini' || item.source_type === 'curated' || item.source_org?.toLowerCase().includes('relief');
        return {
          ...item,
          signal_type: item.signal_type ?? (isIntel ? 'intelligence' : 'gdelt'),
        };
      }),
  });

  const estimateState = useApiResource({
    endpoint: regionId ? `/api/v1/counterfactual/estimate/${regionId}` : null,
    enabled: Boolean(regionId),
    dependencies: [regionId],
  });

  const charitiesState = useApiResource({
    endpoint: regionId ? `/api/v1/charities?region_id=${regionId}` : null,
    enabled: Boolean(regionId),
    dependencies: [regionId],
  });

  const roundsState = useApiResource({
    endpoint: regionId ? `/api/v1/funding/rounds` : null,
    enabled: Boolean(regionId),
    dependencies: [regionId],
  });

  const loading =
    regionState.loading ||
    trajectoryState.loading ||
    signalsState.loading ||
    newsState.loading ||
    estimateState.loading ||
    charitiesState.loading;

  return {
    region,
    trajectory: trajectoryState.trajectory,
    signals: signalsState.data ?? [],
    news: newsState.data ?? [],
    estimate: estimateState.data ?? null,
    charities: charitiesState.data ?? [],
    rounds: roundsState.data ?? [],
    activeRound: (roundsState.data ?? []).find((r) => r.region_id === regionId && r.status === "active") ?? null,
    scoreBreakdown: region ? summarizeDrivers(region) : [],
    loading,
    source: [
      regionState.source,
      trajectoryState.source,
      signalsState.source,
      newsState.source,
      estimateState.source,
    ].includes("live")
      ? "live"
      : loading
      ? "loading"
      : "error",
  };
}
