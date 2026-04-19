import React, { useMemo, useState } from "react";

function formatMoney(value) {
  if (value >= 1000000000) {
    return `$${(value / 1000000000).toFixed(1)}B`;
  }
  if (value >= 1000000) {
    return `$${(value / 1000000).toFixed(1)}M`;
  }
  return `$${value}`;
}

export default function TimelineScrubber({ caseStudy, onStepChange }) {
  const steps = useMemo(() => caseStudy?.timeline ?? [], [caseStudy]);
  const [activeIndex, setActiveIndex] = useState(Math.max(0, steps.length - 1));
  const activeStep = steps[activeIndex] ?? null;

  React.useEffect(() => {
    setActiveIndex(Math.max(0, steps.length - 1));
  }, [steps]);

  function handleChange(index) {
    setActiveIndex(index);
    onStepChange?.(steps[index], index);
  }

  if (!caseStudy) {
    return null;
  }

  return (
    <section className="rounded-[28px] border border-grey-dark/80 bg-white/[0.03] p-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="text-xs uppercase tracking-[0.28em] text-grey-mid">Timeline scrubber</div>
          <h3 className="mt-2 text-2xl font-semibold text-white">{caseStudy.event}</h3>
        </div>
        <div className="rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-right">
          <div className="text-xs uppercase tracking-[0.2em] text-grey-mid">Cost multiplier</div>
          <div className="mt-1 font-mono text-3xl text-white">{caseStudy.cost_multiplier}x</div>
        </div>
      </div>

      <div className="mt-6 rounded-[24px] border border-grey-dark/70 bg-black/20 p-5">
        <input
          type="range"
          min="0"
          max={Math.max(steps.length - 1, 0)}
          step="1"
          value={activeIndex}
          onChange={(event) => handleChange(Number(event.target.value))}
          className="w-full accent-orange"
        />
        <div className="mt-4 grid gap-4 md:grid-cols-3">
          {steps.map((step, index) => (
            <button
              key={`${step.date}-${step.event}`}
              type="button"
              onClick={() => handleChange(index)}
              className={`rounded-[20px] border p-4 text-left transition ${
                index === activeIndex ? "border-orange bg-orange/10" : "border-grey-dark/70 bg-white/[0.03]"
              }`}
            >
              <div className="text-xs uppercase tracking-[0.2em] text-grey-mid">{step.date}</div>
              <div className="mt-2 text-base font-medium text-white">{step.event}</div>
              <div className="mt-3 font-mono text-lg text-grey-light">Score {step.score}</div>
            </button>
          ))}
        </div>
      </div>

      {activeStep && (
        <div className="mt-6 grid gap-4 lg:grid-cols-2">
          <div className="rounded-[24px] border border-teal-light/30 bg-teal/10 p-5">
            <div className="text-xs uppercase tracking-[0.2em] text-teal-light">Act before this moment</div>
            <div className="mt-2 font-mono text-4xl text-white">{formatMoney(caseStudy.prevention_cost_usd)}</div>
          </div>
          <div className="rounded-[24px] border border-red-alert/30 bg-red-alert/10 p-5">
            <div className="text-xs uppercase tracking-[0.2em] text-red-200">Recover after crossing</div>
            <div className="mt-2 font-mono text-4xl text-white">{formatMoney(caseStudy.recovery_cost_usd)}</div>
          </div>
        </div>
      )}
    </section>
  );
}
