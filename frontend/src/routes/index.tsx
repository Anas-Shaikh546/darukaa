import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useRef, useState } from "react";
import { Layers, X } from "lucide-react";

import { AnalysisResponse } from "@/components/darukaa/AnalysisResponse";
import { Composer } from "@/components/darukaa/Composer";
import { EmptyState } from "@/components/darukaa/EmptyState";
import { EnvironmentalContext } from "@/components/darukaa/EnvironmentalContext";
import {
  emptyContext,
  type Analysis,
  type EnvironmentalGroup,
} from "@/data/darukaa";
import { cn } from "@/lib/utils";
import { postConversationTurn } from "@/lib/api";

const title = "Darukaa — Biodiversity Intelligence";
const description =
  "Darukaa connects soil, climate, land-use and biodiversity variables with retrieved scientific evidence to recommend practical interventions and define what to monitor.";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title },
      { name: "description", content: description },
      { property: "og:title", content: title },
      { property: "og:description", content: description },
    ],
  }),
  component: Workspace,
});

interface Turn {
  id: number;
  query: string;
  analysis: Analysis | null;
  message?: string;
}

interface BackendEnvironment {
  soil?: {
    pH?: number | null;
    organic_carbon?: number | null;
    moisture?: number | null;
  } | null;
  climate?: {
    temperature?: number | null;
    rainfall_category?: string | null;
    rainfall_mm_year?: number | null;
  } | null;
  land?: {
    land_use?: string | null;
    land_cover?: string | null;
  } | null;
  biodiversity?: string | null;
  human_impact?: string | null;
  location?: string | null;
}

interface BackendRecommendation {
  recommendation: string;
  reasoning: {
    variables: string[];
    relationships: string[][];
    explanation: string;
  };
  impacted_metrics: {
    metric: string;
    estimate: string;
    basis: string;
  }[];
  time_horizon: string;
  confidence: number;
  evidence: {
    source: string;
    title: string;
    chunk_id: string;
    used_for: string;
    text: string;
    similarity?: number;
  }[];
  validation: {
    variable_count: number;
    evidence_grounded: boolean;
    numeric_claims_ok: boolean;
    evidence_verification_ok: boolean;
    messages: string[];
    retry_used: boolean;
  };
  monitoring: {
    metric: string;
    why_monitor: string;
    horizon: string;
  }[];
}

function detectedVariable(value: unknown): boolean {
  return value !== null && value !== undefined && value !== "";
}

function mapEnvironmentToContext(
  environment: BackendEnvironment,
): EnvironmentalGroup[] {
  const groups: EnvironmentalGroup[] = [];

  type Variable = EnvironmentalGroup["variables"][number];

  const detectedVar = (label: string, value: unknown): Variable => ({
    label,
    value: String(value),
    state: "detected",
  });

  const soilVariables: Variable[] = [];

  if (detectedVariable(environment.soil?.pH)) {
    soilVariables.push(detectedVar("pH", environment.soil?.pH));
  }

  if (detectedVariable(environment.soil?.organic_carbon)) {
    soilVariables.push(
      detectedVar("Organic carbon", `${environment.soil?.organic_carbon}%`),
    );
  }

  if (detectedVariable(environment.soil?.moisture)) {
    soilVariables.push(detectedVar("Moisture", environment.soil?.moisture));
  }

  if (soilVariables.length > 0) {
    groups.push({
      id: "soil",
      title: "Soil",
      variables: soilVariables,
    });
  }

  const climateVariables: Variable[] = [];

  if (detectedVariable(environment.climate?.temperature)) {
    climateVariables.push(
      detectedVar("Temperature", `${environment.climate?.temperature}°C`),
    );
  }

  if (detectedVariable(environment.climate?.rainfall_category)) {
    climateVariables.push(
      detectedVar("Rainfall", environment.climate?.rainfall_category),
    );
  }

  if (detectedVariable(environment.climate?.rainfall_mm_year)) {
    climateVariables.push(
      detectedVar(
        "Annual rainfall",
        `${environment.climate?.rainfall_mm_year} mm/year`,
      ),
    );
  }

  if (climateVariables.length > 0) {
    groups.push({
      id: "climate",
      title: "Climate",
      variables: climateVariables,
    });
  }

  const landVariables: Variable[] = [];

  if (detectedVariable(environment.land?.land_use)) {
    landVariables.push(detectedVar("Land use", environment.land?.land_use));
  }

  if (detectedVariable(environment.land?.land_cover)) {
    landVariables.push(
      detectedVar("Land cover", environment.land?.land_cover),
    );
  }

  if (landVariables.length > 0) {
    groups.push({
      id: "land",
      title: "Land",
      variables: landVariables,
    });
  }

  if (detectedVariable(environment.biodiversity)) {
    groups.push({
      id: "biodiversity",
      title: "Biodiversity",
      variables: [detectedVar("Status", environment.biodiversity)],
    });
  }

  if (detectedVariable(environment.human_impact)) {
    groups.push({
      id: "human-impact",
      title: "Human impact",
      variables: [detectedVar("Impact", environment.human_impact)],
    });
  }

  if (detectedVariable(environment.location)) {
    groups.push({
      id: "location",
      title: "Location",
      variables: [detectedVar("Region", environment.location)],
    });
  }

  return groups;
}

function mapRecommendationToAnalysis(
  recommendation: BackendRecommendation,
  context: EnvironmentalGroup[],
): Analysis {
  return {
    understanding: [recommendation.reasoning.explanation],
    recommendation: {
      statement: recommendation.recommendation,
      timeHorizon: recommendation.time_horizon,
      confidence: `${Math.round(recommendation.confidence * 100)}%`,
      metrics: recommendation.impacted_metrics.map((metric) => metric.metric),
    },
    context,
    reasoning: recommendation.reasoning.relationships.map((chain, index) => ({
      id: `chain-${index}`,
      origin: chain[0] ?? "Environmental variable",
      steps: chain.slice(1),
    })),
    evidence: recommendation.evidence.map((item, index) => ({
      id: item.chunk_id || `evidence-${index}`,
      source: item.source,
      title: item.title,
      excerpt: item.text,
      relevance: "high",
      similarity: item.similarity,
    })),
    monitoring: recommendation.monitoring.map((item) => ({
      horizon: item.horizon,
      metrics: [
        {
          name: item.metric,
          detail: item.why_monitor,
        },
      ],
    })),
  };
}

function Workspace() {
  const [turns, setTurns] = useState<Turn[]>([]);
  const [context, setContext] = useState<EnvironmentalGroup[]>(emptyContext);
  const [contextOpen, setContextOpen] = useState(false);
  const [aboutOpen, setAboutOpen] = useState(false);
  const [pending, setPending] = useState(false);
  const scroller = useRef<HTMLDivElement | null>(null);
  const [conversationId] = useState(() => crypto.randomUUID());

  const hasSignal = turns.some((turn) => turn.analysis !== null);

  useEffect(() => {
    scroller.current?.scrollTo({
      top: scroller.current.scrollHeight,
      behavior: "smooth",
    });
  }, [turns, pending]);

  const runQuery = async (query: string) => {
    const id = Date.now();

    setTurns((prev) => [
      ...prev,
      {
        id,
        query,
        analysis: null,
      },
    ]);

    setPending(true);

    try {
      const response = await postConversationTurn({
        conversation_id: conversationId,
        message: query,
      });

      if (response.environment) {
        const mappedContext = mapEnvironmentToContext(
          response.environment as BackendEnvironment,
        );

        setContext(mappedContext);

        if (response.recommendation) {
          const analysis = mapRecommendationToAnalysis(
            response.recommendation as BackendRecommendation,
            mappedContext,
          );

          setTurns((prev) =>
            prev.map((turn) =>
              turn.id === id
                ? {
                    ...turn,
                    message: response.message,
                    analysis,
                  }
                : turn,
            ),
          );
        } else {
          setTurns((prev) =>
            prev.map((turn) =>
              turn.id === id
                ? {
                    ...turn,
                    message: response.message,
                  }
                : turn,
            ),
          );
        }
      } else {
        setTurns((prev) =>
          prev.map((turn) =>
            turn.id === id
              ? {
                  ...turn,
                  message: response.message,
                }
              : turn,
          ),
        );
      }
    } catch (error) {
      console.error("Darukaa conversation request failed:", error);

      setTurns((prev) =>
        prev.map((turn) =>
          turn.id === id
            ? {
                ...turn,
                message:
                  "Unable to connect to the Darukaa intelligence service. Please check that the backend is running and try again.",
              }
            : turn,
        ),
      );
    } finally {
      setPending(false);
    }
  };

  const reset = () => {
    setTurns([]);
    setContext(emptyContext);
    setPending(false);
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="flex min-h-screen">
        <main className="flex min-w-0 flex-1 flex-col">
          <header className="flex h-16 shrink-0 items-center justify-between border-b border-border px-4 md:px-8">
            <div>
              <p className="label-field text-primary">Darukaa</p>
              <p className="measure text-[0.6875rem] text-muted-foreground">
                Biodiversity Intelligence
              </p>
            </div>

            <button
              type="button"
              onClick={() => setContextOpen((open) => !open)}
              className="inline-flex items-center gap-2 border border-border px-3 py-2 text-[0.6875rem] uppercase tracking-wider text-muted-foreground lg:hidden"
            >
              <Layers className="size-3.5" />
              Environment
            </button>
          </header>

          <div className="flex min-h-0 flex-1">
            <section className="flex min-w-0 flex-1 flex-col">
              <div
                ref={scroller}
                className="min-h-0 flex-1 overflow-y-auto px-5 py-8 md:px-10 md:py-10 lg:px-14"
              >
                <div className="mx-auto max-w-3xl">
                  {!hasSignal && turns.length === 0 ? (
                    <EmptyState onQuery={runQuery} />
                  ) : (
                    <div className="space-y-10">
                      {turns.map((turn) => (
                        <div key={turn.id} className="space-y-8">
                          <div>
                            <p className="label-field mb-3 text-muted-foreground">
                              Environmental query
                            </p>
                            <p className="text-[1rem] leading-relaxed text-foreground">
                              {turn.query}
                            </p>
                          </div>

                          {turn.message && !turn.analysis && (
                            <div className="border-l-2 border-border px-5 py-4">
                              <p className="text-[0.9375rem] leading-relaxed text-muted-foreground">
                                {turn.message}
                              </p>
                            </div>
                          )}

                          {turn.analysis && (
                            <AnalysisResponse analysis={turn.analysis} />
                          )}
                        </div>
                      ))}

                      {pending && (
                        <div className="border-l-2 border-primary px-5 py-4">
                          <p className="measure text-[0.75rem] text-muted-foreground">
                            Connecting environmental variables…
                          </p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>

              <div className="shrink-0 border-t border-border px-5 py-4 md:px-10 lg:px-14">
                <div className="mx-auto max-w-3xl">
                  <Composer onSubmit={runQuery} disabled={pending} />
                </div>
              </div>
            </section>

            <aside
              className={cn(
                "hidden w-[21rem] shrink-0 border-l border-border bg-card lg:block",
                contextOpen && "block",
              )}
            >
              <EnvironmentalContext groups={context} hasSignal={hasSignal} />
            </aside>
          </div>
        </main>
      </div>

      {contextOpen && (
        <div className="fixed inset-0 z-40 bg-background lg:hidden">
          <div className="flex h-16 items-center justify-between border-b border-border px-5">
            <p className="label-field">Environmental context</p>
            <button
              type="button"
              onClick={() => setContextOpen(false)}
              className="inline-flex size-9 items-center justify-center border border-border"
              aria-label="Close environmental context"
            >
              <X className="size-4" />
            </button>
          </div>

          <EnvironmentalContext groups={context} hasSignal={hasSignal} />
        </div>
      )}

      {aboutOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-foreground/20 p-5">
          <div className="w-full max-w-lg border border-border bg-background p-7 shadow-panel">
            <div className="flex items-start justify-between gap-6">
              <div>
                <p className="label-field text-primary">About Darukaa</p>
                <h2 className="display-serif mt-2 text-2xl">
                  Biodiversity Intelligence
                </h2>
              </div>

              <button
                type="button"
                onClick={() => setAboutOpen(false)}
                className="inline-flex size-9 shrink-0 items-center justify-center border border-border"
                aria-label="Close"
              >
                <X className="size-4" />
              </button>
            </div>

            <p className="mt-6 text-[0.9375rem] leading-relaxed text-muted-foreground">
              Darukaa connects environmental variables, curated scientific
              relationships, and retrieved evidence to produce grounded
              biodiversity recommendations and monitoring plans.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}