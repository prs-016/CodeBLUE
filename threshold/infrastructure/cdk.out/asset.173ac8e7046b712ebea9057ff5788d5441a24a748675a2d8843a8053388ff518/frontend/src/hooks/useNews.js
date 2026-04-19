import { useApiResource } from "./useApiResource";

export default function useNews(regionId) {
  const regionNews = useApiResource({
    endpoint: regionId ? `/api/v1/news/${regionId}` : null,
    enabled: Boolean(regionId),
    dependencies: [regionId],
    transform: (rows) =>
      rows.map((item) => ({
        ...item,
        signal_type:
          item.signal_type ??
          (item.source_org?.toLowerCase().includes("relief") ? "reliefweb" : "gdelt"),
      })),
  });

  const attentionGap = useApiResource({
    endpoint: "/api/v1/news/attention-gap",
  });

  return {
    items: regionNews.data ?? [],
    attentionGap: attentionGap.data ?? [],
    loading: regionNews.loading || attentionGap.loading,
    source: regionNews.source,
  };
}
