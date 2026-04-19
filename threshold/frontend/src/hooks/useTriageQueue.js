import { useMemo } from "react";
import { mockRegions } from "./mockData";
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
  const fallbackData = useMemo(
    () => mockRegions.map(normalizeTriageRegion).sort((a, b) => a.days_to_threshold - b.days_to_threshold),
    []
  );

  const state = useApiResource({
    endpoint: `/api/v1/triage${query}`,
    fallbackData,
    initialData: fallbackData,
    dependencies: [query],
    transform: (rows) => rows.map(normalizeTriageRegion),
  });

  return {
    ...state,
    queue: state.data ?? [],
  };
}
