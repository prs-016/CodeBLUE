import { useMemo } from "react";
import { useApiResource, buildQuery } from "./useApiResource";

function normalizeTriageRegion(region) {
  const score = region.threshold_proximity_score ?? region.current_score ?? 0;
  return {
    ...region,
    id: region.id ?? region.region_id,
    name: region.name,
    current_score: score,
    threshold_proximity_score: score,
    threat_type: region.threat_type ?? region.primary_threat ?? "thermal",
  };
}

export default function useTriageQueue(filters = {}) {
  const query = useMemo(() => buildQuery(filters), [filters]);
  const state = useApiResource({
    endpoint: `/api/v1/triage${query}`,
    dependencies: [query],
    transform: (rows) => rows.map(normalizeTriageRegion),
  });
  return { ...state, queue: state.data ?? [] };
}
