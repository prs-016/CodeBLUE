import { useMemo } from "react";
import { useApiResource } from "./useApiResource";

function normalizeRegion(region) {
  if (!region) return null;
  const score = region.threshold_proximity_score ?? region.current_score ?? 0;
  return {
    ...region,
    id: region.id ?? region.region_id,
    current_score: score,
    threshold_proximity_score: score,
    primary_threat: region.primary_threat ?? region.threat_type ?? "thermal",
    threat_type: region.threat_type ?? region.primary_threat ?? "thermal",
    primary_driver:
      region.primary_driver ??
      (region.sst_anomaly ? `SST Anomaly +${region.sst_anomaly}°C` : "Composite stress acceleration"),
    committed_funding_usd:
      region.committed_funding_usd ??
      Math.max(0, (region.modeled_intervention_cost || 0) - (region.funding_gap || 0)),
  };
}

export function useRegions() {
  const state = useApiResource({
    endpoint: "/api/v1/regions",
    transform: (rows) => rows.map(normalizeRegion),
  });
  return { ...state, regions: state.data ?? [] };
}

export function useRegion(regionId) {
  const state = useApiResource({
    endpoint: regionId ? `/api/v1/regions/${regionId}` : null,
    enabled: Boolean(regionId),
    dependencies: [regionId],
    transform: normalizeRegion,
  });
  return { ...state, region: state.data };
}

export function useRegionTrajectory(regionId) {
  const state = useApiResource({
    endpoint: regionId ? `/api/v1/regions/${regionId}/trajectory` : null,
    enabled: Boolean(regionId),
    dependencies: [regionId],
  });
  return {
    ...state,
    trajectory: state.data?.trajectory ?? [],
    daysToThreshold: state.data?.days_to_threshold ?? null,
  };
}
