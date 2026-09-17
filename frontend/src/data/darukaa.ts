/**
 * Mock analysis data for Darukaa's UI states.
 * Shapes here mirror what the FastAPI backend is expected to return, so each
 * component can later be fed real data without structural changes.
 */

export type VariableState = "detected" | "not-provided" | "potentially-relevant";

export interface EnvironmentalVariable {
  label: string;
  value?: string;
  state: VariableState;
  note?: string;
}

export interface EnvironmentalGroup {
  id: string;
  title: string;
  variables: EnvironmentalVariable[];
}

export interface ReasoningChain {
  id: string;
  origin: string;
  steps: string[];
}

export interface EvidenceItem {
  id: string;
  source: string;
  title: string;
  excerpt: string;
  relevance: "high" | "moderate";
  similarity?: number;
}

export interface MonitoringMetric {
  name: string;
  detail: string;
}

export interface MonitoringPhase {
  horizon: string;
  metrics: MonitoringMetric[];
}

export interface Recommendation {
  statement: string;
  timeHorizon: string;
  confidence: string;
  metrics: string[];
}

export interface Analysis {
  understanding: string[];
  recommendation: Recommendation;
  context: EnvironmentalGroup[];
  reasoning: ReasoningChain[];
  evidence: EvidenceItem[];
  monitoring: MonitoringPhase[];
}

export const emptyContext: EnvironmentalGroup[] = [
  {
    id: "soil",
    title: "Soil",
    variables: [
      { label: "Organic carbon", state: "not-provided" },
      { label: "pH", state: "not-provided" },
    ],
  },
  {
    id: "climate",
    title: "Climate",
    variables: [{ label: "Rainfall", state: "not-provided" }],
  },
  {
    id: "land-use",
    title: "Land use",
    variables: [{ label: "System", state: "not-provided" }],
  },
  {
    id: "biodiversity",
    title: "Biodiversity",
    variables: [{ label: "Observed", state: "not-provided" }],
  },
];

export const sampleAnalysis: Analysis = {
  understanding: [
    "Soil organic carbon is reported at 0.3%, which sits at the low end of the range associated with stable soil structure.",
    "Rainfall is described as low, so water availability is a limiting condition rather than a background variable.",
    "The land is under wheat as a monoculture, meaning habitat structure is uniform across the parcel.",
  ],
  recommendation: {
    statement:
      "Consider implementing agroforestry — introducing woody perennial rows into the wheat system to rebuild soil carbon, improve water retention, and restore habitat structure.",
    timeHorizon: "3–7 years to measurable ecological response",
    confidence: "Moderate–high, grounded in three retrieved sources",
    metrics: ["Soil organic carbon", "Water retention", "Habitat connectivity", "Species richness"],
  },
  context: [
    {
      id: "soil",
      title: "Soil",
      variables: [
        { label: "Organic carbon", value: "0.3%", state: "detected" },
        { label: "pH", state: "not-provided" },
      ],
    },
    {
      id: "climate",
      title: "Climate",
      variables: [
        { label: "Rainfall", value: "Low", state: "detected" },
        { label: "Temperature regime", state: "potentially-relevant" },
      ],
    },
    {
      id: "land-use",
      title: "Land use",
      variables: [
        { label: "System", value: "Wheat monoculture", state: "detected" },
        { label: "Field margins", state: "potentially-relevant" },
      ],
    },
    {
      id: "biodiversity",
      title: "Biodiversity",
      variables: [{ label: "Observed", state: "not-provided" }],
    },
  ],
  reasoning: [
    {
      id: "soc",
      origin: "SOC",
      steps: [
        "Soil structure",
        "Water retention",
        "Plant survival",
        "Vegetation",
        "Habitat quality",
        "Biodiversity",
      ],
    },
    {
      id: "rainfall",
      origin: "Rainfall",
      steps: ["Water availability", "Vegetation productivity"],
    },
    {
      id: "land-use",
      origin: "Land-use intensity",
      steps: [
        "Habitat fragmentation",
        "Habitat connectivity",
        "Species movement",
        "Species richness",
      ],
    },
  ],
  evidence: [
    {
      id: "fao",
      source: "FAO",
      title: "Soil Organic Carbon: The Hidden Potential",
      excerpt:
        "Soil organic carbon underpins soil structure, water-holding capacity and nutrient cycling; losses reduce the capacity of soils to support plant growth and the organisms that depend on it.",
      relevance: "high",
      similarity: 0.87,
    },
    {
      id: "ipcc",
      source: "IPCC AR6 WGII",
      title: "Climate Change 2022: Impacts, Adaptation and Vulnerability",
      excerpt:
        "Reduced water availability constrains vegetation productivity in dryland cropping systems, with consequences for the habitats those systems provide.",
      relevance: "high",
      similarity: 0.81,
    },
    {
      id: "plos",
      source: "PLOS ONE",
      title: "Agroforestry Practices Promote Biodiversity and Natural Resource Diversity",
      excerpt:
        "Agroforestry systems supported greater structural and species diversity than adjacent monocultures, alongside improvements in soil and water indicators.",
      relevance: "moderate",
      similarity: 0.76,
    },
  ],
  monitoring: [
    {
      horizon: "Short term",
      metrics: [{ name: "Soil moisture", detail: "Tracks water availability and retention." }],
    },
    {
      horizon: "Medium term",
      metrics: [
        { name: "Soil organic carbon", detail: "Tracks soil-health response." },
        { name: "Habitat diversity", detail: "Tracks habitat structure and connectivity." },
      ],
    },
    {
      horizon: "Long term",
      metrics: [{ name: "Species richness", detail: "Tracks biodiversity response." }],
    },
  ],
};

export const suggestionPrompts = [
  "My soil organic carbon is low…",
  "How is drought affecting biodiversity?",
  "What can I do about monoculture?",
  "Help me improve habitat quality.",
];

export const sampleQuery =
  "My soil organic carbon is 0.3%, rainfall is low, and I am growing wheat as a monoculture.";

export const recentConversations = [
  { id: "c1", title: "Wheat monoculture, low SOC", meta: "Today" },
  { id: "c2", title: "Riparian buffer, grazing pressure", meta: "Tuesday" },
  { id: "c3", title: "Drought response, native grassland", meta: "Last week" },
];

export const stateLabel: Record<VariableState, string> = {
  detected: "Detected",
  "not-provided": "Not provided",
  "potentially-relevant": "Potentially relevant",
};
