import { useApiResource } from "./useApiResource";
import { useRegion, useRegionTrajectory } from "./useRegions";

function summarizeDrivers(region) {
  if (region?.breakdown) return region.breakdown;
  
  // Fallback for missing breakdown
  return [
    {
      key: "thermal",
      label: "Water Temperature",
      value: region?.t_degc ?? 0,
      detail: "Live sensor data",
    },
    {
      key: "oxygen",
      label: "Dissolved Oxygen",
      value: region?.o2ml_l ?? 0,
      detail: "Hypoxia monitor",
    },
    {
      key: "productivity",
      label: "Chlorophyll",
      value: region?.chlora ?? 0,
      detail: "Ecosystem primary production",
    },
    {
      key: "stability",
      label: "Political Stability",
      value: region?.goldstein ?? 0,
      detail: "GDELT Narrative Score",
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
      rows.map((item) => ({
        ...item,
        signal_type:
          item.signal_type ??
          (item.source_org?.toLowerCase().includes("relief") ? "reliefweb" : "gdelt"),
      })),
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
