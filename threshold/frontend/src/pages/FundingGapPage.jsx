import FundingGapRadar from '../components/FundingGap/FundingGapRadar';

export default function FundingGapPage() {
  return (
    <div className="w-full h-full bg-navy overflow-auto p-8">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-end mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">The Funding Gap Radar</h1>
            <p className="text-grey-mid max-w-2xl">
              Visualizing the discrepancy between ecological crisis severity and active financial intervention. Regions in the bottom-right quadrant represent systemic market failures requiring immediate capital injection.
            </p>
          </div>
          <div className="flex space-x-4">
            <div className="bg-navy border border-grey-dark px-4 py-2 rounded">
              <div className="text-xs text-grey-mid uppercase tracking-widest">Total Monitored</div>
              <div className="text-xl font-bold text-teal-light">8 Regions</div>
            </div>
            <div className="bg-navy border border-red-alert/50 px-4 py-2 rounded shadow-[0_0_10px_rgba(192,57,43,0.2)]">
              <div className="text-xs text-grey-mid uppercase tracking-widest">Max Gap</div>
              <div className="text-xl font-bold text-red-alert">$12.0M</div>
            </div>
          </div>
        </div>
        
        <FundingGapRadar />
      </div>
    </div>
  );
}
