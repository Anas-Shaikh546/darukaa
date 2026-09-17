import type { MonitoringPhase } from "@/data/darukaa";

export function MonitoringTimeline({ phases }: { phases: MonitoringPhase[] }) {
  return (
    <ol className="relative border-l border-border-strong pl-6">
      {phases.map((phase, pi) => (
        <li
          key={phase.horizon}
          className="reveal relative pb-7 last:pb-0"
          style={{ animationDelay: `${pi * 120}ms` }}
        >
          <span
            aria-hidden
            className="absolute -left-[1.8125rem] top-1 size-2.5 rounded-full border border-border-strong bg-background"
          >
            <span className="absolute inset-[3px] rounded-full bg-soil" />
          </span>
          <p className="label-field text-soil">{phase.horizon}</p>
          <div className="mt-3 space-y-3">
            {phase.metrics.map((m) => (
              <div key={m.name}>
                <p className="measure text-[0.875rem] font-medium text-foreground">{m.name}</p>
                <p className="text-[0.8125rem] leading-relaxed text-muted-foreground">
                  {m.detail}
                </p>
              </div>
            ))}
          </div>
        </li>
      ))}
    </ol>
  );
}
