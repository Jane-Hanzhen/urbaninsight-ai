import type { MockAnalysis } from "@/types/urban";

export const londonBoroughNames = [
  "Barking and Dagenham",
  "Barnet",
  "Bexley",
  "Brent",
  "Bromley",
  "Camden",
  "City of London",
  "Croydon",
  "Ealing",
  "Enfield",
  "Greenwich",
  "Hackney",
  "Hammersmith and Fulham",
  "Haringey",
  "Harrow",
  "Havering",
  "Hillingdon",
  "Hounslow",
  "Islington",
  "Kensington and Chelsea",
  "Kingston upon Thames",
  "Lambeth",
  "Lewisham",
  "Merton",
  "Newham",
  "Redbridge",
  "Richmond upon Thames",
  "Southwark",
  "Sutton",
  "Tower Hamlets",
  "Waltham Forest",
  "Wandsworth",
  "Westminster"
] as const;

export const mockAnalysis: MockAnalysis = {
  boroughName: "Camden",
  overallScore: 82,
  rank: 4,
  summary:
    "shows strong urban vitality, led by commercial intensity and public-service access. Ecological resilience is the clearest opportunity for targeted improvement.",
  dimensions: [
    {
      label: "Economic",
      score: 86,
      description: "High commercial activity and strong service density."
    },
    {
      label: "Social",
      score: 79,
      description: "Well connected public services and education access."
    },
    {
      label: "Ecological",
      score: 72,
      description: "Moderate green access with room for air-quality gains."
    }
  ],
  contributions: [
    { dimension: "Economic", contribution: 38 },
    { dimension: "Social", contribution: 34 },
    { dimension: "Ecological", contribution: 28 }
  ],
  indicators: [],
  strengths: [
    {
      title: "Commercial vitality",
      detail: "Dense services and diverse local activity support a resilient economy."
    },
    {
      title: "Education access",
      detail: "Most residents can reach high-quality education within 15 minutes."
    },
    {
      title: "Connected neighbourhoods",
      detail: "Strong transit access links residential areas to jobs and services."
    }
  ],
  weaknesses: [
    {
      title: "Limited green coverage",
      detail: "Accessible green space remains below the wider London benchmark."
    },
    {
      title: "Air-quality pressure",
      detail: "Traffic corridors create persistent exposure in several neighbourhoods."
    }
  ],
  recommendations: [
    {
      title: "Build a green corridor network",
      detail: "Connect pocket parks, school grounds, and low-traffic streets along priority walking routes.",
      priority: "High"
    },
    {
      title: "Target transport emissions",
      detail: "Expand bus-priority and zero-emission delivery zones around the highest-exposure corridors.",
      priority: "High"
    },
    {
      title: "Protect mixed-use clusters",
      detail: "Support affordable workspace near transit to preserve local economic diversity.",
      priority: "Medium"
    }
  ]
};
