import { useState } from "react";
import { ArrowUp, Paperclip } from "lucide-react";
import { suggestionPrompts } from "@/data/darukaa";

export function Composer({
  onSubmit,
  showSuggestions,
}: {
  onSubmit: (value: string) => void;
  showSuggestions: boolean;
}) {
  const [value, setValue] = useState("");

  const submit = (text: string) => {
    const trimmed = text.trim();
    if (!trimmed) return;
    onSubmit(trimmed);
    setValue("");
  };

  return (
    <div className="border-t border-border bg-background/95 px-5 py-4 backdrop-blur md:px-10">
      <div className="mx-auto max-w-3xl">
        {showSuggestions ? (
          <div className="mb-3 flex flex-wrap gap-2">
            {suggestionPrompts.map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => setValue(s)}
                className="rounded-sm border border-border px-2.5 py-1.5 text-[0.75rem] text-muted-foreground transition-colors hover:border-border-strong hover:text-foreground"
              >
                {s}
              </button>
            ))}
          </div>
        ) : null}

        <form
          onSubmit={(e) => {
            e.preventDefault();
            submit(value);
          }}
          className="flex items-end gap-3 border border-border-strong bg-card px-4 py-3 shadow-panel focus-within:border-ring"
        >
          <button
            type="button"
            aria-label="Attach field data (coming soon)"
            title="Attach field data — coming soon"
            className="pb-1 text-muted-foreground/70 transition-colors hover:text-muted-foreground"
          >
            <Paperclip className="size-4" />
          </button>

          <label className="sr-only" htmlFor="darukaa-query">
            Environmental query
          </label>
          <textarea
            id="darukaa-query"
            rows={1}
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                submit(value);
              }
            }}
            placeholder="Describe your ecosystem, land, soil, climate, or biodiversity concern…"
            className="max-h-40 min-h-8 flex-1 resize-none bg-transparent text-[0.9375rem] leading-relaxed text-foreground outline-none placeholder:text-muted-foreground/80"
          />

          <button
            type="submit"
            disabled={!value.trim()}
            aria-label="Run analysis"
            className="flex size-8 items-center justify-center rounded-sm bg-primary text-primary-foreground transition-opacity disabled:opacity-30"
          >
            <ArrowUp className="size-4" />
          </button>
        </form>

        <p className="measure mt-2 text-[0.6875rem] text-muted-foreground">
          Darukaa reasons from what you describe and cites retrieved scientific material.
        </p>
      </div>
    </div>
  );
}
