import type { ReasoningChain } from "@/data/darukaa";

export function ReasoningPath({ chains }: { chains: ReasoningChain[] }) {
  return (
    <div className="space-y-7">
      {chains.map((chain, ci) => (
        <div key={chain.id} className="reveal" style={{ animationDelay: `${ci * 120}ms` }}>
          <div className="flex items-center gap-3">
            <span className="measure rounded-sm bg-primary px-2 py-1 text-[0.6875rem] uppercase tracking-wider text-primary-foreground">
              {chain.origin}
            </span>
            <span
              aria-hidden
              className="trace-line h-px flex-1 bg-border-strong"
              style={{ animationDelay: `${ci * 120 + 100}ms` }}
            />
          </div>

          <ol className="mt-3 flex flex-wrap items-center gap-x-3 gap-y-2 pl-1">
            {chain.steps.map((step, si) => (
              <li
                key={step}
                className="reveal flex items-center gap-3"
                style={{ animationDelay: `${ci * 120 + si * 90 + 140}ms` }}
              >
                <span className="flex items-center gap-2">
                  <span aria-hidden className="size-1.5 rounded-full bg-moss" />
                  <span className="text-[0.8125rem] text-foreground">{step}</span>
                </span>
                {si < chain.steps.length - 1 ? (
                  <span aria-hidden className="measure text-muted-foreground">
                    →
                  </span>
                ) : null}
              </li>
            ))}
          </ol>
        </div>
      ))}
    </div>
  );
}
