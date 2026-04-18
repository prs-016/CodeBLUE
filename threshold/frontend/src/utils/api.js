// We can use process.env in Vite via import.meta.env, but we fallback to typical localhost
const API_BASE = (import.meta && import.meta.env && import.meta.env.VITE_API_URL) || 'http://localhost:8000';

export const api = {
  getRegions: () => fetch(`${API_BASE}/api/v1/regions`).then(r => r.json()),
  getRegion: (id) => fetch(`${API_BASE}/api/v1/regions/${id}`).then(r => r.json()),
  getTriage: (params = '') => fetch(`${API_BASE}/api/v1/triage?${params}`).then(r => r.json()),
  getFundingGap: () => fetch(`${API_BASE}/api/v1/funding/gap`).then(r => r.json()),
  getCounterfactuals: () => fetch(`${API_BASE}/api/v1/counterfactual/cases`).then(r => r.json()),
  getCounterfactual: (id) => fetch(`${API_BASE}/api/v1/counterfactual/cases/${id}`).then(r => r.json()),
  getFundingRounds: () => fetch(`${API_BASE}/api/v1/funding/rounds`).then(r => r.json()),
  getFundingRound: (id) => fetch(`${API_BASE}/api/v1/funding/rounds/${id}`).then(r => r.json()),
  contribute: (roundId, data) => fetch(`${API_BASE}/api/v1/funding/rounds/${roundId}/contribute`, {
    method: 'POST', body: JSON.stringify(data), headers: {'Content-Type': 'application/json'}
  }).then(r => r.json()),
  getNews: (regionId) => fetch(`${API_BASE}/api/v1/news/${regionId}`).then(r => r.json()),
  getImpact: () => fetch(`${API_BASE}/api/v1/funding/impact`).then(r => r.json()),
}
