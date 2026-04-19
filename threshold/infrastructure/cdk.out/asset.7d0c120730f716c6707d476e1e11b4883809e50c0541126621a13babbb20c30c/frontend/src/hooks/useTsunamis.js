import { useApiResource } from "./useApiResource";

const EMPTY_ARRAY = [];

export default function useTsunamis() {
  const { data, loading, error, source } = useApiResource({
    endpoint: "/api/v1/tsunamis",
    fallbackData: EMPTY_ARRAY,
  });

  return {
    tsunamis: data || EMPTY_ARRAY,
    loading,
    error,
    source,
  };
}
