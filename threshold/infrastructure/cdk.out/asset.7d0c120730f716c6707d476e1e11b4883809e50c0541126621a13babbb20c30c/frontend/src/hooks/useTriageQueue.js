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
  // Serialize filters to a string so `useMemo` dep comparison is by value,
  // not by object reference — prevents infinite refetch on default `filters = {}`
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const query = useMemo(() => buildQuery(filters), [JSON.stringify(filters)]);
  const state = useApiResource({
    endpoint: `/api/v1/triage${query}`,
    // No extra `dependencies` — endpoint already encodes the query string.
    transform: (rows) => rows.map(normalizeTriageRegion),
  });
  return { ...state, queue: state.data ?? [] };
}
