import { useCallback, useState } from "react";
import { api } from "../utils/api";

export function useRiskAssessment() {
  const [quick, setQuick] = useState(null);
  const [enrich, setEnrich] = useState(null);
  const [loadingQuick, setLoadingQuick] = useState(false);
  const [loadingEnrich, setLoadingEnrich] = useState(false);
  const [error, setError] = useState(null);

  const assess = useCallback(async (lat, lon) => {
    setQuick(null);
    setEnrich(null);
    setError(null);
    setLoadingQuick(true);
    setLoadingEnrich(true);

    // Both requests fire immediately; phase 1 renders as soon as it resolves
    const quickPromise = api.riskQuick(lat, lon);
    const enrichPromise = api.riskEnrich(lat, lon);

    try {
      const quickResult = await quickPromise;
      setQuick(quickResult);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoadingQuick(false);
    }

    try {
      const enrichResult = await enrichPromise;
      setEnrich(enrichResult);
    } catch (err) {
      // Don't overwrite a quick error; just surface in enrich state
      setEnrich({ headlines: [], charities: [], errors: { news: err.message, charities: err.message } });
    } finally {
      setLoadingEnrich(false);
    }
  }, []);

  const clear = useCallback(() => {
    setQuick(null);
    setEnrich(null);
    setError(null);
  }, []);

  return { quick, enrich, loadingQuick, loadingEnrich, error, assess, clear };
}
