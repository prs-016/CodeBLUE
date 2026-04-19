import { useMemo } from "react";
import { getMockNews, mockFundingGap } from "./mockData";
import { useApiResource } from "./useApiResource";

export default function useNews(regionId) {
  const fallbackNews = useMemo(() => getMockNews(regionId), [regionId]);
  const regionNews = useApiResource({
    endpoint: regionId ? `/api/v1/news/${regionId}` : null,
    fallbackData: fallbackNews,
    initialData: fallbackNews,
    enabled: Boolean(regionId),
    dependencies: [regionId],
  });

  const attentionGap = useApiResource({
    endpoint: "/api/v1/news/attention-gap",
    fallbackData: mockFundingGap.map((region) => ({
      region_id: region.region_id,
      name: region.name,
      severity_score: region.threshold_score,
      normalized_attention_score: Math.max(0, region.threshold_score - region.attention_gap),
      attention_gap: region.attention_gap,
    })),
    initialData: [],
  });

  return {
    items: regionNews.data ?? fallbackNews,
    attentionGap: attentionGap.data ?? [],
    loading: regionNews.loading || attentionGap.loading,
    source: [regionNews.source, attentionGap.source].includes("fallback") ? "fallback" : "live",
  };
}
