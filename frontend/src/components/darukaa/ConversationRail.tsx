import { Info, Plus, X } from "lucide-react";
import { recentConversations } from "@/data/darukaa";
import { cn } from "@/lib/utils";

interface Props {
  activeId: string;
  onNewAnalysis: () => void;
  onSelect: (id: string) => void;
  onAbout: () => void;
  onClose?: () => void;
}

export function ConversationRail({
  activeId,
  onNewAnalysis,
  onSelect,
  onAbout,
  onClose,
}: Props) {
  return (
    <div className="flex h-full flex-col bg-rail text-rail-foreground">
      <div className="flex items-start justify-between gap-3 border-b border-rail-border px-5 py-5">
        <div>
          <p className="display-serif text-lg leading-none tracking-wide">Darukaa</p>
          <p className="label-field mt-2 text-rail-muted">Biodiversity Intelligence</p>
        </div>
        {onClose ? (
          <button
            type="button"
            onClick={onClose}
            aria-label="Close navigation"
            className="rounded-sm p-1 text-rail-muted transition-colors hover:text-rail-foreground"
          >
            <X className="size-4" />
          </button>
        ) : null}
      </div>

      <div className="px-5 py-4">
        <button
          type="button"
          onClick={onNewAnalysis}
          className="flex w-full items-center gap-2 rounded-sm border border-rail-border px-3 py-2 text-left text-sm transition-colors hover:border-rail-muted"
        >
          <Plus className="size-3.5 text-rail-muted" />
          New analysis
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-5">
        <p className="label-field text-rail-muted">Recent</p>
        <ul className="mt-3 space-y-px">
          {recentConversations.map((c) => {
            const active = c.id === activeId;
            return (
              <li key={c.id}>
                <button
                  type="button"
                  onClick={() => onSelect(c.id)}
                  aria-current={active ? "true" : undefined}
                  className={cn(
                    "group relative w-full py-2.5 pl-3 pr-2 text-left transition-colors",
                    active ? "text-rail-foreground" : "text-rail-muted hover:text-rail-foreground",
                  )}
                >
                  <span
                    className={cn(
                      "absolute left-0 top-2.5 bottom-2.5 w-px",
                      active ? "bg-primary" : "bg-rail-border",
                    )}
                  />
                  <span className="block truncate text-sm leading-snug">{c.title}</span>
                  <span className="measure mt-1 block text-[0.6875rem] opacity-70">{c.meta}</span>
                </button>
              </li>
            );
          })}
        </ul>
      </div>

      <div className="border-t border-rail-border px-5 py-4">
        <button
          type="button"
          onClick={onAbout}
          className="flex items-center gap-2 text-xs text-rail-muted transition-colors hover:text-rail-foreground"
        >
          <Info className="size-3.5" />
          About Darukaa
        </button>
      </div>
    </div>
  );
}
