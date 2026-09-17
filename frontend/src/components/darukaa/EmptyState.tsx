const investigations = [
  {
    title: "Low soil carbon under continuous cropping",
    detail: "Connect soil structure and water retention to habitat quality.",
  },
  {
    title: "Drought pressure on a grassland parcel",
    detail: "Trace water availability through vegetation productivity.",
  },
  {
    title: "Monoculture and habitat fragmentation",
    detail: "Examine connectivity and species movement across the parcel.",
  },
];

export function EmptyState({ onPick }: { onPick: (value: string) => void }) {
  return (
    <div className="reveal max-w-2xl py-6">
      <p className="label-field">Begin an investigation</p>
      <h2 className="display-serif mt-4 text-[2rem] leading-tight text-foreground">
        Understand the ecology of your land.
      </h2>
      <p className="mt-4 max-w-xl text-[0.9375rem] leading-relaxed text-muted-foreground">
        Describe your soil, climate, land use, or biodiversity conditions. Darukaa connects
        environmental variables with scientific evidence to identify practical interventions.
      </p>

      <ul className="mt-9 divide-y divide-border border-y border-border">
        {investigations.map((item) => (
          <li key={item.title}>
            <button
              type="button"
              onClick={() => onPick(item.title)}
              className="group w-full py-4 text-left"
            >
              <span className="block text-[0.9375rem] leading-snug text-foreground transition-colors group-hover:text-primary">
                {item.title}
              </span>
              <span className="mt-1 block text-[0.8125rem] text-muted-foreground">
                {item.detail}
              </span>
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
