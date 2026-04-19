import { useApiResource } from "./useApiResource";

function normalizeCaseSummary(item) {
  return {
    ...item,
    event: item.event ?? item.event_name,
    region:
      item.region ??
      (item.region_id
        ? item.region_id.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())
        : undefined),
    prevention_cost_usd: item.prevention_cost_usd ?? item.prevention_cost,
    recovery_cost_usd: item.recovery_cost_usd ?? item.recovery_cost,
  };
}

export default function useCounterfactual({ caseId, regionId } = {}) {
  const casesState = useApiResource({
    endpoint: "/api/v1/counterfactual/cases",
    transform: (data) => (Array.isArray(data) ? data.map(normalizeCaseSummary) : data),
  });

  const caseState = useApiResource({
    endpoint: caseId ? `/api/v1/counterfactual/cases/${caseId}` : null,
    enabled: Boolean(caseId),
    dependencies: [caseId],
    transform: (data) => (data && typeof data === "object" ? normalizeCaseSummary(data) : data),
  });

  const estimateState = useApiResource({
    endpoint: regionId ? `/api/v1/counterfactual/estimate/${regionId}` : null,
    enabled: Boolean(regionId),
    dependencies: [regionId],
  });

  return {
    cases: casesState.data ?? [],
    selectedCase: caseState.data ?? null,
    estimate: estimateState.data ?? null,
    loading: casesState.loading || caseState.loading || estimateState.loading,
    source: [casesState.source, caseState.source, estimateState.source].includes("live")
      ? "live"
      : "loading",
  };
}
