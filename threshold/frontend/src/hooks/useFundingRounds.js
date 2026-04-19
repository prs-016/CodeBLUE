import { useMemo } from "react";
import {
  getMockCharities,
  mockFundingRounds,
  mockImpactCases,
  mockTransactions,
  mockTransparency,
} from "./mockData";
import { useApiResource } from "./useApiResource";

export default function useFundingRounds() {
  const roundsState = useApiResource({
    endpoint: "/api/v1/funding/rounds",
    fallbackData: mockFundingRounds,
    initialData: mockFundingRounds,
  });

  const impactState = useApiResource({
    endpoint: "/api/v1/funding/impact",
    fallbackData: mockImpactCases,
    initialData: mockImpactCases,
  });

  const transactionsState = useApiResource({
    endpoint: "/api/v1/fund/transactions",
    fallbackData: mockTransactions,
    initialData: mockTransactions,
  });

  const transparencyState = useApiResource({
    endpoint: "/api/v1/fund/transparency",
    fallbackData: mockTransparency,
    initialData: mockTransparency,
  });

  const charityMap = useMemo(() => {
    return roundsState.data.reduce((accumulator, round) => {
      accumulator[round.region_id] = getMockCharities(round.region_id);
      return accumulator;
    }, {});
  }, [roundsState.data]);

  return {
    rounds: roundsState.data ?? [],
    impact: impactState.data ?? [],
    transactions: transactionsState.data ?? [],
    transparency: transparencyState.data ?? mockTransparency,
    charitiesByRegion: charityMap,
    loading: roundsState.loading || impactState.loading || transactionsState.loading || transparencyState.loading,
    source:
      [roundsState.source, impactState.source, transactionsState.source, transparencyState.source].includes("fallback")
        ? "fallback"
        : "live",
  };
}
