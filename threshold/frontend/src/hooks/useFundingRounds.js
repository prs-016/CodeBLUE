import { useMemo } from "react";
import { useApiResource } from "./useApiResource";

export default function useFundingRounds() {
  const roundsState = useApiResource({
    endpoint: "/api/v1/funding/rounds",
  });

  const impactState = useApiResource({
    endpoint: "/api/v1/funding/impact",
    transform: (rows) =>
      rows.map((item) => ({
        ...item,
        event: item.event ?? item.event_name,
        region:
          item.region ??
          item.region_id?.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
        recovery_cost_usd: item.recovery_cost_usd ?? item.recovery_cost,
        prevention_cost_usd: item.prevention_cost_usd ?? item.prevention_cost,
        impact_score_delta:
          item.impact_score_delta ?? Number(-(item.cost_multiplier / 10).toFixed(1)),
      })),
  });

  const transactionsState = useApiResource({
    endpoint: "/api/v1/fund/transactions",
  });

  const transparencyState = useApiResource({
    endpoint: "/api/v1/fund/transparency",
  });

  const charityMap = useMemo(() => {
    return (roundsState.data ?? []).reduce((accumulator, round) => {
      accumulator[round.region_id] = [];
      return accumulator;
    }, {});
  }, [roundsState.data]);

  return {
    rounds: roundsState.data ?? [],
    impact: impactState.data ?? [],
    transactions: transactionsState.data ?? [],
    transparency: transparencyState.data ?? { total_volume_usd: 0, total_transactions: 0, smart_contract_address: "" },
    charitiesByRegion: charityMap,
    loading:
      roundsState.loading ||
      impactState.loading ||
      transactionsState.loading ||
      transparencyState.loading,
    source: [roundsState.source, impactState.source, transactionsState.source, transparencyState.source].includes(
      "live"
    )
      ? "live"
      : "loading",
  };
}
