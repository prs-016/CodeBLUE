import { useEffect, useMemo, useState } from "react";

const API_BASE = (import.meta?.env?.VITE_API_URL) || "http://localhost:8000";

async function readJson(endpoint, options = {}) {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    throw new Error(`Request failed for ${endpoint}: ${response.status}`);
  }

  return response.json();
}

export function useApiResource({
  endpoint,
  fallbackData,
  initialData,
  transform,
  enabled = true,
  dependencies = [],
  requestOptions,
}) {
  const [data, setData] = useState(initialData ?? fallbackData);
  const [loading, setLoading] = useState(Boolean(enabled));
  const [error, setError] = useState(null);
  const [source, setSource] = useState("loading");

  useEffect(() => {
    let active = true;

    async function load() {
      if (!enabled || !endpoint) {
        setLoading(false);
        setSource("disabled");
        return;
      }

      setLoading(true);
      setError(null);

      try {
        const response = await readJson(endpoint, requestOptions);
        if (!active) {
          return;
        }

        const nextData = transform ? transform(response) : response;
        const isEmpty =
          nextData == null ||
          (Array.isArray(nextData) && nextData.length === 0) ||
          (typeof nextData === "object" && !Array.isArray(nextData) && Object.keys(nextData).length === 0);

        if (isEmpty && fallbackData != null) {
          setData(fallbackData);
          setSource("fallback");
          return;
        }

        setData(nextData);
        setSource("live");
      } catch (nextError) {
        if (!active) {
          return;
        }

        setError(nextError);
        setData(fallbackData);
        setSource("fallback");
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    load();

    return () => {
      active = false;
    };
  }, [enabled, endpoint, ...dependencies]);

  return useMemo(
    () => ({
      data,
      loading,
      error,
      source,
      isFallback: source === "fallback",
      isLive: source === "live",
    }),
    [data, error, loading, source]
  );
}

export function buildQuery(params = {}) {
  const search = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      search.set(key, String(value));
    }
  });

  const query = search.toString();
  return query ? `?${query}` : "";
}
