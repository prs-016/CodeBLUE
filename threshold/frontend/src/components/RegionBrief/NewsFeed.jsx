import React from "react";

function groupItems(items) {
  return {
    intelligence: items.filter((item) => item.signal_type === "intelligence"),
    gdelt: items.filter((item) => item.signal_type === "gdelt"),
  };
}

function NewsColumn({ title, eyebrow, items }) {
  return (
    <div className="rounded-[24px] border border-grey-dark/70 bg-black/20 p-5">
      <div className="text-xs uppercase tracking-[0.25em] text-grey-mid">{eyebrow}</div>
      <h4 className="mt-2 text-xl font-semibold text-white">{title}</h4>
      <div className="mt-4 space-y-3">
        {items.map((item) => (
          <article key={item.id} className="rounded-[18px] border border-grey-dark/60 bg-white/[0.03] p-4">
            <div className="flex items-center justify-between gap-3">
              <div className="text-sm font-medium text-white">{item.title}</div>
              <div className="text-xs uppercase tracking-[0.16em] text-grey-mid">{item.date}</div>
            </div>
            <p className="mt-2 text-sm text-grey-mid">{item.body_summary}</p>
            <div className="mt-3 text-xs uppercase tracking-[0.2em] text-teal-light">{item.source_org}</div>
          </article>
        ))}
      </div>
    </div>
  );
}

export default function NewsFeed({ items = [] }) {
  const grouped = groupItems(items);

  return (
    <section className="rounded-[28px] border border-grey-dark/80 bg-white/[0.03] p-6">
      <div>
        <div className="text-xs uppercase tracking-[0.28em] text-grey-mid">News intelligence</div>
        <h3 className="mt-2 text-2xl font-semibold text-white">Live Operations vs Media Attention</h3>
        <p className="mt-1 text-sm text-grey-mid">
          Continuous AI intelligence via Gemini identifies live crisis operations from disparate ground truth sources. GDELT isolates macroscopic public media visibility.
        </p>
      </div>

      <div className="mt-6 grid gap-4 xl:grid-cols-2">
        <NewsColumn title="Situation reports" eyebrow="AI Live Intelligence" items={grouped.intelligence} />
        <NewsColumn title="Attention signal" eyebrow="GDELT" items={grouped.gdelt} />
      </div>
    </section>
  );
}
