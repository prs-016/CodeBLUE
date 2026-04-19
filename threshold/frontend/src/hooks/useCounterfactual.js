import { useMemo } from "react";
import {
  getMockCounterfactualCase,
  getMockCounterfactualEstimate,
  mockImpactCases,
} from "./mockData";
import { useApiResource } from "./useApiResource";

export default function useCounterfactual({ caseId, regionId } = {}) {
  const casesState = useApiResource({
    endpoint: "/api/v1/counterfactual/cases",
    fallbackData: mockImpactCases,
    initialData: mockImpactCases,
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
