const CASE_STUDIES = [
  {
    case_id: "california_sardine",
    region_id: "california_current",
    region: "California Current",
    event: "California Sardine Collapse",
    year_crossed: 1947,
    prevention_cost_usd: 8000000,
    recovery_cost_usd: 800000000,
    cost_multiplier: 100,
    early_warning_date: "1939-01-01",
    last_intervention_date: "1945-01-01",
    threshold_crossed_date: "1947-06-01",
    data_source: "CalCOFI 1949 retrospective analysis",
  },
  {
    case_id: "gbr_2016",
    region_id: "great_barrier_reef",
    region: "Great Barrier Reef",
    event: "GBR Mass Bleaching Event",
    year_crossed: 2016,
    prevention_cost_usd: 25000000,
    recovery_cost_usd: 400000000,
    cost_multiplier: 16,
    early_warning_date: "2014-01-01",
    last_intervention_date: "2015-06-01",
    threshold_crossed_date: "2016-02-01",
    data_source: "NOAA Coral Reef Watch + EM-DAT",
  },
  {
    case_id: "arabian_sea_dead_zone",
    region_id: "arabian_sea",
    region: "Arabian Sea",
    event: "Arabian Sea Dead Zone Expansion",
    year_crossed: 2008,
    prevention_cost_usd: 50000000,
    recovery_cost_usd: 2100000000,
    cost_multiplier: 42,
    early_warning_date: "2000-01-01",
    last_intervention_date: "2005-01-01",
    threshold_crossed_date: "2008-01-01",
    data_source: "NASA Ocean Color + World Bank",
  },
  {
    case_id: "baltic_hypoxia",
    region_id: "baltic_sea",
    region: "Baltic Sea",
    event: "Baltic Hypoxic Dead Zone",
    year_crossed: 1980,
    prevention_cost_usd: 30000000,
    recovery_cost_usd: 890000000,
    cost_multiplier: 30,
    early_warning_date: "1960-01-01",
    last_intervention_date: "1975-01-01",
    threshold_crossed_date: "1980-01-01",
    data_source: "HELCOM Baltic Sea reports + EM-DAT",
  },
  {
    case_id: "gulf_dead_zone",
    region_id: "gulf_of_mexico",
    region: "Gulf of Mexico",
    event: "Gulf Dead Zone Annual Expansion",
    year_crossed: 1985,
    prevention_cost_usd: 200000000,
    recovery_cost_usd: 2800000000,
    cost_multiplier: 14,
    early_warning_date: "1970-01-01",
    last_intervention_date: "1980-01-01",
    threshold_crossed_date: "1985-01-01",
    data_source: "NASA Ocean Color + NOAA ERDDAP + EM-DAT",
  },
];

const DEMO_CHARITIES = [
  { ein: "52-1693387", name: "WWF", overall_score: 89.4, region_id: "coral_triangle" },
  { ein: "53-0242652", name: "The Nature Conservancy", overall_score: 92.1, region_id: "california_current" },
  { ein: "RW3W-001", name: "WorldFish Center", overall_score: 86.8, region_id: "mekong_delta", source: "reliefweb_3w" },
  { ein: "26-1737731", name: "Coral Restoration Foundation", overall_score: 88.2, region_id: "great_barrier_reef" },
  { ein: "23-7245152", name: "Ocean Conservancy", overall_score: 85.6, region_id: "gulf_of_mexico" },
];

const REGION_BASE = [
  {
    id: "great_barrier_reef",
    name: "Great Barrier Reef",
    lat: -18.2871,
    lon: 147.6992,
    current_score: 8.4,
    threshold_proximity_score: 8.4,
    days_to_threshold: 47,
    funding_gap: 8400000,
    committed_funding_usd: 1600000,
    primary_threat: "thermal",
    threat_type: "thermal",
    alert_level: 4,
    bleaching_alert_level: 4,
    dhw_current: 9.1,
    sst_anomaly: 2.3,
    sst_anomaly_30d_avg: 2.3,
    primary_driver: "SST Anomaly +2.3°C above 30yr baseline",
    population_affected: 4200000,
    coverage_ratio: 0.16,
  },
  {
    id: "mekong_delta",
    name: "Mekong Delta",
    lat: 10.5,
    lon: 105.5,
    current_score: 7.1,
    threshold_proximity_score: 7.1,
    days_to_threshold: 180,
    funding_gap: 9600000,
    committed_funding_usd: 2400000,
    primary_threat: "hypoxia",
    threat_type: "hypoxia",
    alert_level: 2,
    o2_current: 2.8,
    hypoxia_risk: 0.72,
    primary_driver: "Dissolved O2 at 2.8 ml/L (threshold: 2.0)",
    population_affected: 6100000,
    coverage_ratio: 0.2,
  },
  {
    id: "arabian_sea",
    name: "Arabian Sea",
    lat: 16.5,
    lon: 66.5,
    current_score: 6.8,
    threshold_proximity_score: 6.8,
    days_to_threshold: 290,
    funding_gap: 12000000,
    committed_funding_usd: 1200000,
    primary_threat: "hypoxia",
    threat_type: "hypoxia",
    alert_level: 1,
    o2_current: 3.1,
    hypoxia_risk: 0.65,
    primary_driver: "Expanding dead zone — O2 3.1 ml/L declining at -0.08/yr",
    population_affected: 7900000,
    coverage_ratio: 0.09,
  },
  {
    id: "california_current",
    name: "California Current",
    lat: 36.7783,
    lon: -122.4179,
    current_score: 5.2,
    threshold_proximity_score: 5.2,
    days_to_threshold: 520,
    funding_gap: 3200000,
    committed_funding_usd: 2100000,
    primary_threat: "acidification",
    threat_type: "acidification",
    alert_level: 1,
    co2_yoy_acceleration: 0.034,
    primary_driver: "CO2 acceleration +3.4% YoY above trend",
    population_affected: 2300000,
    coverage_ratio: 0.4,
  },
  {
    id: "gulf_of_mexico",
    name: "Gulf of Mexico",
    lat: 25.2644,
    lon: -89.4375,
    current_score: 6.1,
    threshold_proximity_score: 6.1,
    days_to_threshold: 365,
    funding_gap: 7200000,
    committed_funding_usd: 800000,
    primary_threat: "hypoxia",
    threat_type: "hypoxia",
    alert_level: 2,
    chlorophyll_anomaly: 4.2,
    hypoxia_risk: 0.58,
    primary_driver: "Chlorophyll bloom 4.2x seasonal baseline",
    population_affected: 5100000,
    coverage_ratio: 0.1,
  },
  {
    id: "coral_triangle",
    name: "Coral Triangle",
    lat: 0.5,
    lon: 127.5,
    current_score: 7.8,
    threshold_proximity_score: 7.8,
    days_to_threshold: 95,
    funding_gap: 11000000,
    committed_funding_usd: 2200000,
    primary_threat: "thermal",
    threat_type: "thermal",
    alert_level: 3,
    bleaching_alert_level: 3,
    dhw_current: 6.4,
    sst_anomaly: 1.8,
    sst_anomaly_30d_avg: 1.8,
    primary_driver: "SST Anomaly +1.8°C, DHW 6.4 and rising",
    population_affected: 8400000,
    coverage_ratio: 0.17,
  },
  {
    id: "baltic_sea",
    name: "Baltic Sea",
    lat: 58.5,
    lon: 19.5,
    current_score: 4.8,
    threshold_proximity_score: 4.8,
    days_to_threshold: 730,
    funding_gap: 4100000,
    committed_funding_usd: 3200000,
    primary_threat: "hypoxia",
    threat_type: "hypoxia",
    alert_level: 1,
    o2_current: 3.8,
    hypoxia_risk: 0.42,
    primary_driver: "Persistent hypoxic zone — O2 3.8 ml/L",
    population_affected: 1800000,
    coverage_ratio: 0.43,
  },
  {
    id: "bengal_bay",
    name: "Bay of Bengal",
    lat: 15,
    lon: 89.5,
    current_score: 5.9,
    threshold_proximity_score: 5.9,
    days_to_threshold: 410,
    funding_gap: 8800000,
    committed_funding_usd: 900000,
    primary_threat: "thermal",
    threat_type: "thermal",
    alert_level: 1,
    sst_anomaly: 1.4,
    sst_anomaly_30d_avg: 1.4,
    primary_driver: "SST Anomaly +1.4°C, cyclone intensification risk",
    population_affected: 7200000,
    coverage_ratio: 0.1,
  },
];

function monthlySignal(seriesYears, startYear, fn) {
  const rows = [];
  for (let year = startYear; year < startYear + seriesYears; year += 1) {
    for (let month = 0; month < 12; month += 1) {
      const date = new Date(Date.UTC(year, month, 1));
      rows.push(fn(date, rows.length));
    }
  }
  return rows;
}

const EL_NINO_YEARS = new Set([1983, 1998, 2010, 2016, 2023]);

function getSeasonalPhase(regionId) {
  return ["great_barrier_reef", "coral_triangle"].includes(regionId) ? 0 : Math.PI;
}

function buildStressSignals(region) {
  return monthlySignal(76, 1949, (date, index) => {
    const year = date.getUTCFullYear();
    const month = date.getUTCMonth();
    const seasonal = Math.sin((month / 12) * Math.PI * 2 + getSeasonalPhase(region.id));
    const warmingTrend = (year - 1949) * 0.018;
    const elNinoBoost = EL_NINO_YEARS.has(year) ? 0.8 : 0;
    const baseTemp = region.primary_threat === "thermal" ? 0.7 : 0.25;
    const sstAnomaly = Number((baseTemp + warmingTrend + seasonal * 0.55 + elNinoBoost).toFixed(2));
    const o2Current = Number((6.5 - (year - 1949) * 0.012 + seasonal * 0.08 - (region.hypoxia_risk || 0) * 2.8).toFixed(2));
    const chlorophyllAnomaly = Number((((region.chlorophyll_anomaly || 1.3) * 0.35) + Math.max(0, seasonal) * 1.2 + (year > 2000 ? 0.2 : 0)).toFixed(2));
    const co2Regional = Number((315 + (year - 1958) * 1.62 + Math.sin((month / 12) * Math.PI * 2) * 2.7).toFixed(2));
    const thresholdProximityScore = Number(
      Math.max(
        0.8,
        Math.min(10, (region.current_score || 5) - 2 + warmingTrend * 0.4 + elNinoBoost * 1.8 + Math.max(0, seasonal) * 0.9)
      ).toFixed(2)
    );

    return {
      date: date.toISOString().slice(0, 10),
      sst_anomaly: sstAnomaly,
      o2_current: o2Current,
      chlorophyll_anomaly: chlorophyllAnomaly,
      co2_regional_ppm: co2Regional,
      nitrate_anomaly: Number((0.3 + Math.max(0, seasonal) * 0.6 + index * 0.001).toFixed(2)),
      threshold_proximity_score: thresholdProximityScore,
    };
  });
}

function buildTrajectory(region) {
  const start = new Date("2026-04-18T00:00:00Z");
  const points = [];
  for (let i = 0; i < 24; i += 1) {
    const date = new Date(start);
    date.setUTCDate(date.getUTCDate() + i * 30);
    const progress = i / 23;
    const nextScore = Math.min(
      10,
      Number((region.current_score + (8.1 - region.current_score) * progress + Math.sin(progress * Math.PI * 2) * 0.2).toFixed(2))
    );
    points.push({
      date: date.toISOString().slice(0, 10),
      predicted_score: nextScore,
      low: Number(Math.max(0, nextScore - 0.55).toFixed(2)),
      high: Number(Math.min(10, nextScore + 0.65).toFixed(2)),
    });
  }
  return {
    region_id: region.id,
    days_to_threshold: region.days_to_threshold,
    trajectory: points,
  };
}

function buildNews(region) {
  return [
    {
      id: `${region.id}-rw-1`,
      title: `${region.name}: Coastal systems report signals escalating stress`,
      date: "2026-04-17",
      country: region.name,
      disaster_type: region.primary_threat === "thermal" ? "Marine Ecosystem" : "Flood",
      source_org: "ReliefWeb",
      body_summary: `Operational reporting confirms active disruption pressure in ${region.name}.`,
      url: "https://reliefweb.int/",
      crisis_active_flag: region.current_score >= 7,
      urgency_score: Number(region.current_score.toFixed(1)),
      signal_type: "reliefweb",
    },
    {
      id: `${region.id}-gdelt-1`,
      title: `${region.name}: Media attention diverges from ecological severity`,
      date: "2026-04-16",
      country: region.name,
      disaster_type: "Media Attention",
      source_org: "GDELT",
      body_summary: `Coverage intensity remains below modeled severity for ${region.name}.`,
      url: "https://www.gdeltproject.org/",
      crisis_active_flag: false,
      urgency_score: Number((Math.max(1, region.current_score - 2.2)).toFixed(1)),
      signal_type: "gdelt",
      attention_score: Number((Math.max(0.8, region.current_score - 2.1)).toFixed(1)),
    },
  ];
}

function buildFundingRound(region, index) {
  const target = Math.max(1000000, Math.round(region.funding_gap * 0.95));
  const raised = Math.round(region.committed_funding_usd * 0.6);
  const charity = DEMO_CHARITIES.find((item) => item.region_id === region.id) || DEMO_CHARITIES[0];
  return {
    id: `FR-00${index + 1}`,
    region_id: region.id,
    region_name: region.name,
    threat_type: region.primary_threat,
    status: index < 4 ? "Open" : "Closed",
    target_amount: target,
    raised_amount: raised,
    deadline: "2026-05-31",
    cost_multiplier: Math.round(6 + region.current_score * 1.4),
    charity_ein: charity.ein,
    charity_name: charity.name,
    verified_score: charity.overall_score,
    progress_report_required: true,
    round_summary: `${region.primary_driver} is driving the current emergency round.`,
  };
}

export const mockRegions = REGION_BASE.map((region) => ({
  ...region,
  current_score: region.current_score ?? region.threshold_proximity_score,
}));

export const mockFundingGap = mockRegions.map((region) => ({
  region_id: region.id,
  name: region.name,
  threshold_score: region.current_score,
  funding_gap: region.funding_gap,
  threat_type: region.primary_threat,
  population_affected: region.population_affected,
  attention_gap: Number((region.current_score - region.coverage_ratio * 5).toFixed(2)),
  coverage_ratio: region.coverage_ratio,
  committed_funding_usd: region.committed_funding_usd,
  primary_driver: region.primary_driver,
}));

export const mockFundingRounds = mockRegions.map(buildFundingRound);

export const mockImpactCases = CASE_STUDIES.map((caseStudy, index) => ({
  ...caseStudy,
  impact_score_delta: Number((-1.2 - index * 0.35).toFixed(1)),
  households_supported: 250000 + index * 90000,
  hectares_protected: 12000 + index * 2500,
}));

export const mockTransactions = [
  {
    hash: "5KtQh7NmDemoA",
    round_id: "FR-001",
    amount_usd: 50,
    timestamp: "2026-04-18T13:12:00Z",
    status: "Confirmed",
  },
  {
    hash: "5KtQh7NmDemoB",
    round_id: "FR-002",
    amount_usd: 340000,
    timestamp: "2026-04-16T09:41:00Z",
    status: "Confirmed",
  },
];

export const mockTransparency = {
  total_volume_usd: 15400000,
  total_transactions: 24501,
  smart_contract_address: "ThResH1Demo9zQ2",
  recent_blocks: mockTransactions,
};

export function getMockRegion(regionId) {
  const region = mockRegions.find((item) => item.id === regionId);
  if (!region) {
    return mockRegions[0];
  }

  return {
    ...region,
    active_situation_reports: region.current_score >= 7 ? 4 : 1,
    scientific_event_flag: region.primary_threat === "thermal",
    stress_composite: region.current_score,
    bleaching_risk_flag: (region.bleaching_alert_level || 0) >= 3,
    news_attention_gap: Number((region.current_score - region.coverage_ratio * 7).toFixed(1)),
  };
}

export function getMockTrajectory(regionId) {
  return buildTrajectory(getMockRegion(regionId));
}

export function getMockStressSignals(regionId) {
  return buildStressSignals(getMockRegion(regionId));
}

export function getMockNews(regionId) {
  return buildNews(getMockRegion(regionId));
}

export function getMockCounterfactualEstimate(regionId) {
  const matchedCase = CASE_STUDIES.find((item) => item.region_id === regionId);
  const region = getMockRegion(regionId);
  if (matchedCase) {
    return {
      region_id: regionId,
      prevention_cost: matchedCase.prevention_cost_usd,
      recovery_cost: matchedCase.recovery_cost_usd,
      cost_multiplier: matchedCase.cost_multiplier,
      breakdown: {
        monitoring: Math.round(matchedCase.prevention_cost_usd * 0.18),
        intervention: Math.round(matchedCase.prevention_cost_usd * 0.82),
        ag_loss: Math.round(matchedCase.recovery_cost_usd * 0.22),
        infra_loss: Math.round(matchedCase.recovery_cost_usd * 0.35),
        fishery_loss: Math.round(matchedCase.recovery_cost_usd * 0.28),
      },
      optimal_intervention_type: region.primary_threat === "thermal" ? "Thermal stress mitigation" : "Nutrient reduction and oxygen recovery",
    };
  }

  const prevention = Math.round(region.funding_gap * 1.25);
  return {
    region_id: regionId,
    prevention_cost: prevention,
    recovery_cost: prevention * 9,
    cost_multiplier: 9,
    breakdown: {
      monitoring: Math.round(prevention * 0.2),
      intervention: Math.round(prevention * 0.8),
      ag_loss: Math.round(prevention * 1.5),
      infra_loss: Math.round(prevention * 2.3),
      fishery_loss: Math.round(prevention * 3.2),
    },
    optimal_intervention_type: "Rapid resilience deployment",
  };
}

export function getMockCounterfactualCase(caseId) {
  const caseStudy = CASE_STUDIES.find((item) => item.case_id === caseId) || CASE_STUDIES[0];
  return {
    ...caseStudy,
    timeline: [
      {
        date: caseStudy.early_warning_date,
        event: "Early warning signal detected",
        score: 4.2,
      },
      {
        date: caseStudy.last_intervention_date,
        event: "Last viable intervention window",
        score: 7.6,
      },
      {
        date: caseStudy.threshold_crossed_date,
        event: "Threshold crossed",
        score: 10,
      },
    ],
  };
}

export function getMockCharities(regionId) {
  return DEMO_CHARITIES.filter((item) => !regionId || item.region_id === regionId).map((item) => ({
    ...item,
    accountability_score: 86,
    financial_score: 88,
    program_expense_ratio: 0.82,
    eligible_for_disbursement: true,
    active_regions: [item.region_id],
  }));
}
