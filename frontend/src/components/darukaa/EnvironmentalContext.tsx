import { stateLabel, type EnvironmentalGroup, type VariableState } from "@/data/darukaa";
import { cn } from "@/lib/utils";

const dot: Record<VariableState, string> = {
  detected: "bg-primary",
  "not-provided": "bg-border-strong",
  "potentially-relevant": "bg-clay",
};

export function EnvironmentalContext({
  groups,
  hasSignal,
}: {
  groups: EnvironmentalGroup[];
  hasSignal: boolean;
}) {
  const detected = groups.reduce(
    (n, g) => n + g.variables.filter((v) => v.state === "detected").length,
    0,
  );

  return (
    <section aria-labelledby="env-context-title" className="contour h-full overflow-y-auto">
      <header className="border-b border-border bg-paper-deep/60 px-6 py-5 backdrop-blur-[1px]">
        <h2 id="env-context-title" className="display-serif text-base">
          Environmental Context
        </h2>
        <p className="measure mt-1.5 text-[0.6875rem] text-muted-foreground">
          {hasSignal ? `${detected} variables detected from conversation` : "Awaiting description"}
        </p>
      </header>

      <div className="divide-y divide-border">
        {groups.map((group, gi) => (
          <div
            key={group.id}
            className="reveal px-6 py-5"
            style={{ animationDelay: `${gi * 70}ms` }}
          >
            <p className="label-field">{group.title}</p>
            <dl className="mt-3 space-y-3.5">
              {group.variables.map((v) => (
                <div key={v.label} className="flex items-baseline gap-3">
                  <span
                    aria-hidden
                    className={cn("mt-1.5 size-1.5 shrink-0 rounded-full", dot[v.state])}
                  />
                  <div className="min-w-0 flex-1">
                    <dt className="text-[0.8125rem] leading-tight text-muted-foreground">
                      {v.label}
                    </dt>
                    <dd
                      className={cn(
                        "measure mt-1 text-sm",
                        v.state === "detected"
                          ? "font-medium text-foreground"
                          : "text-[0.75rem] uppercase tracking-wider text-muted-foreground/80",
                      )}
                    >
                      {v.value ?? stateLabel[v.state]}
                    </dd>
                  </div>
                </div>
              ))}
            </dl>
          </div>
        ))}
      </div>

      <p className="border-t border-border px-6 py-5 text-[0.75rem] leading-relaxed text-muted-foreground">
        Values are read from what you describe. Nothing is inferred or filled in.
      </p>
    </section>
  );
}
