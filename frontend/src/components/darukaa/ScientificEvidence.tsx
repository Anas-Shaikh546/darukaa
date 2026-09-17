import { useState } from "react";
import { ChevronDown } from "lucide-react";
import type { EvidenceItem } from "@/data/darukaa";
import { cn } from "@/lib/utils";

export function ScientificEvidence({ items }: { items: EvidenceItem[] }) {
  const [open, setOpen] = useState<string | null>(items[0]?.id ?? null);

  return (
    <ul className="divide-y divide-border border-y border-border">
      {items.map((item, i) => {
        const isOpen = open === item.id;
        return (
          <li key={item.id} className="reveal" style={{ animationDelay: `${i * 90}ms` }}>
            <button
              type="button"
              onClick={() => setOpen(isOpen ? null : item.id)}
              aria-expanded={isOpen}
              className="flex w-full items-start gap-4 py-4 text-left"
            >
              <span className="measure w-24 shrink-0 pt-0.5 text-[0.6875rem] uppercase tracking-widest text-primary">
                {item.source}
              </span>
              <span className="min-w-0 flex-1">
                <span className="block text-[0.9375rem] leading-snug text-foreground">
                  {item.title}
                </span>
                <span className="measure mt-1.5 flex flex-wrap items-center gap-x-4 gap-y-1 text-[0.6875rem] uppercase tracking-wider text-muted-foreground">
                  <span
                    className={cn(
                      item.relevance === "high" ? "text-moss" : "text-muted-foreground",
                    )}
                  >
                    {item.relevance} relevance
                  </span>
                  {item.similarity ? <span>similarity {item.similarity.toFixed(2)}</span> : null}
                </span>
              </span>
              <ChevronDown
                className={cn(
                  "mt-1 size-4 shrink-0 text-muted-foreground transition-transform duration-300",
                  isOpen && "rotate-180",
                )}
              />
            </button>

            <div
              className={cn(
                "grid transition-all duration-300 ease-out",
                isOpen ? "grid-rows-[1fr] opacity-100" : "grid-rows-[0fr] opacity-0",
              )}
            >
              <div className="overflow-hidden">
                <blockquote className="mb-5 ml-28 border-l-2 border-accent pl-4 font-serif text-[0.9375rem] leading-relaxed text-foreground/85">
                  {item.excerpt}
                </blockquote>
              </div>
            </div>
          </li>
        );
      })}
    </ul>
  );
}
