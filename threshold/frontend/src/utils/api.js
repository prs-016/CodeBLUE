const API_BASE = import.meta?.env?.VITE_API_URL || "http://localhost:8000";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    throw new Error(`API request failed for ${path}: ${response.status}`);
  }

  return response.json();
}

export const api = {
  getRegions: () => request("/api/v1/regions"),
  getRegion: (id) => request(`/api/v1/regions/${id}`),
  getRegionTrajectory: (id) => request(`/api/v1/regions/${id}/trajectory`),
  getStressSignals: (id) => request(`/api/v1/regions/${id}/stress-signals`),
  getTriage: (query = "") => request(`/api/v1/triage${query ? `?${query}` : ""}`),
  getFundingGap: () => request("/api/v1/funding/gap"),
  getFundingRounds: () => request("/api/v1/funding/rounds"),
  getFundingRound: (id) => request(`/api/v1/funding/rounds/${id}`),
  contribute: (roundId, payload) =>
    request(`/api/v1/funding/rounds/${roundId}/contribute`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  getImpact: () => request("/api/v1/funding/impact"),
  getNews: (regionId) => request(`/api/v1/news/${regionId}`),
  getCounterfactualCases: () => request("/api/v1/counterfactual/cases"),
  getCounterfactualCase: (caseId) => request(`/api/v1/counterfactual/cases/${caseId}`),
  getCounterfactualEstimate: (regionId) => request(`/api/v1/counterfactual/estimate/${regionId}`),
  getTransactions: () => request("/api/v1/fund/transactions"),
  getTransparency: () => request("/api/v1/fund/transparency"),
  riskQuick: (lat, lon) =>
    request("/api/v1/risk-assessment/quick", {
      method: "POST",
      body: JSON.stringify({ lat, lon }),
    }),
  riskEnrich: (lat, lon) =>
    request("/api/v1/risk-assessment/enrich", {
      method: "POST",
      body: JSON.stringify({ lat, lon }),
    }),
};
