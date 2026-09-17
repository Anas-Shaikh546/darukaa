import type { Analysis } from "@/data/darukaa";
import { MonitoringTimeline } from "./MonitoringTimeline";
import { ReasoningPath } from "./ReasoningPath";
import { ScientificEvidence } from "./ScientificEvidence";

function SectionHeading({ index, title }: { index: string; title: string }) {
  return (
    <div className="mb-5 flex items-baseline gap-3">
      <span className="measure text-[0.6875rem] text-muted-foreground">{index}</span>
      <h3 className="display-serif text-[1.0625rem]">{title}</h3>
      <span aria-hidden className="h-px flex-1 bg-border" />
    </div>
  );
}

export function AnalysisResponse({ analysis }: { analysis: Analysis }) {
  const { understanding, recommendation, reasoning, evidence, monitoring } = analysis;

  return (
    <article className="reveal space-y-12">
      <section>
        <SectionHeading index="01" title="Understanding" />
        <ul className="space-y-3">
          {understanding.map((line) => (
            <li key={line} className="flex gap-3 text-[0.9375rem] leading-relaxed text-foreground">
              <span aria-hidden className="mt-2.5 size-1 shrink-0 rounded-full bg-moss" />
              {line}
            </li>
          ))}
        </ul>
      </section>

      <section>
        <SectionHeading index="02" title="Reasoning Path" />
        <div className="border border-border bg-card p-6 shadow-panel">
          <ReasoningPath chains={reasoning} />
        </div>
      </section>

      <section>
        <SectionHeading index="03" title="Scientific Evidence" />
        <p className="mb-4 text-[0.8125rem] leading-relaxed text-muted-foreground">
          This analysis is grounded in retrieved scientific material. Expand any item to inspect the
          supporting passage.
        </p>
        <ScientificEvidence items={evidence} />
      </section>

      <section aria-labelledby="recommendation-title">
        <div className="border-l-2 border-primary bg-secondary/60 px-6 py-6 shadow-panel">
          <p id="recommendation-title" className="label-field text-primary">
            Recommendation
          </p>
          <p className="display-serif mt-3 text-[1.375rem] leading-snug text-foreground">
            {recommendation.statement}
          </p>

          <dl className="mt-6 grid gap-5 border-t border-border pt-5 sm:grid-cols-2">
            <div>
              <dt className="label-field">Time horizon</dt>
              <dd className="measure mt-2 text-[0.875rem] text-foreground">
                {recommendation.timeHorizon}
              </dd>
            </div>
            <div>
              <dt className="label-field">Confidence</dt>
              <dd className="measure mt-2 text-[0.875rem] text-foreground">
                {recommendation.confidence}
              </dd>
            </div>
            <div className="sm:col-span-2">
              <dt className="label-field">Impacted environmental metrics</dt>
              <dd className="mt-2 flex flex-wrap gap-2">
                {recommendation.metrics.map((m) => (
                  <span
                    key={m}
                    className="measure border border-border-strong px-2 py-1 text-[0.6875rem] uppercase tracking-wider text-foreground"
                  >
                    {m}
                  </span>
                ))}
              </dd>
            </div>
          </dl>
        </div>
      </section>

      <section>
        <SectionHeading index="04" title="Impact & Monitoring" />
        <MonitoringTimeline phases={monitoring} />
      </section>
    </article>
  );
}
