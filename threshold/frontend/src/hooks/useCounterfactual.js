import { useMemo } from "react";
import {
  getMockCounterfactualCase,
  getMockCounterfactualEstimate,
  mockImpactCases,
} from "./mockData";
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
    fallbackData: mockImpactCases,
    initialData: mockImpactCases,
    transform: (data) => Array.isArray(data) ? data.map(normalizeCaseSummary) : data,
  });

  const fallbackCase = useMemo(
    () => (caseId ? getMockCounterfactualCase(caseId) : null),
    [caseId]
  );

  const caseState = useApiResource({
    endpoint: caseId ? `/api/v1/counterfactual/cases/${caseId}` : null,
    fallbackData: fallbackCase,
    initialData: fallbackCase,
    enabled: Boolean(caseId),
    dependencies: [caseId],
    transform: (data) => data && typeof data === "object" ? normalizeCaseSummary(data) : data,
  });

  const fallbackEstimate = useMemo(
    () => (regionId ? getMockCounterfactualEstimate(regionId) : null),
    [regionId]
  );

  const estimateState = useApiResource({
    endpoint: regionId ? `/api/v1/counterfactual/estimate/${regionId}` : null,
    fallbackData: fallbackEstimate,
    initialData: fallbackEstimate,
    enabled: Boolean(regionId),
    dependencies: [regionId],
  });

  return {
    cases: casesState.data ?? [],
    selectedCase: caseState.data ?? fallbackCase,
    estimate: estimateState.data ?? fallbackEstimate,
    loading: casesState.loading || caseState.loading || estimateState.loading,
    source:
      [casesState.source, caseState.source, estimateState.source].includes("fallback")
        ? "fallback"
        : "live",
  };
}
