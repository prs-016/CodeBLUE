import { useApiResource } from "./useApiResource";
import { useRegion, useRegionTrajectory } from "./useRegions";

function summarizeDrivers(region) {
  return [
    {
      key: "thermal",
      label: "Thermal Stress",
      value: region?.sst_anomaly_30d_avg ?? region?.sst_anomaly ?? 0,
      detail: region?.bleaching_alert_level
        ? `Alert ${region.bleaching_alert_level}/4`
        : "No reef alert",
    },
    {
      key: "oxygen",
      label: "Oxygen Loss",
      value: region?.hypoxia_risk ?? Math.max(0, 1 - (region?.o2_current || 5) / 6),
      detail: region?.o2_current ? `${region.o2_current} ml/L` : "Proxy estimate",
    },
    {
      key: "carbon",
      label: "Carbon Pressure",
      value: region?.co2_yoy_acceleration ?? 0,
      detail: region?.co2_yoy_acceleration
        ? `${(region.co2_yoy_acceleration * 100).toFixed(1)}% YoY accel.`
        : "Keeling-linked proxy",
    },
    {
      key: "nutrients",
      label: "Nutrient Load",
      value: region?.chlorophyll_anomaly ?? 0,
      detail: region?.chlorophyll_anomaly
        ? `${region.chlorophyll_anomaly}x seasonal baseline`
        : "Baseline loading",
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
