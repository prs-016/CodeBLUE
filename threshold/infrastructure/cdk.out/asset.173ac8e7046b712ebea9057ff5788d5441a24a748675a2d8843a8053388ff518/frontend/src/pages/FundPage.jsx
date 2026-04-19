// Frontend wrapper for FundDashboard
import FundDashboard from '../components/Fund/FundDashboard';

export default function FundPage() {
  return (
    <div className="w-full h-full bg-navy overflow-auto p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-white mb-2 ml-4">THRESHOLD FUND</h1>
        <p className="text-grey-mid max-w-2xl mb-8 ml-4">
          Direct, verifiable, on-chain capital deployment triggered precisely when ecological thresholds draw critically close, bypassing structural market failures.
        </p>
        
        <FundDashboard />

        <div className="mt-16 mb-8 border-t border-grey-dark pt-8 px-4">
          <h2 className="text-2xl font-bold text-teal-light mb-6">How It Works</h2>
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            {[
              {s: 1, text: "ML detects region approaching threshold"},
              {s: 2, text: "Funding round opens automatically"},
              {s: 3, text: "Verified charities matched to region"},
              {s: 4, text: "Funds collected transparently via Stripe/Solana"},
              {s: 5, text: "Impact measured back in ocean metrics"}
            ].map((step) => (
              <div key={step.s} className="bg-grey-dark/30 border border-grey-dark p-4 rounded-lg flex flex-col relative overflow-hidden">
                <div className="absolute top-2 right-2 text-6xl font-black text-navy/50 pointer-events-none">{step.s}</div>
                <div className="text-teal font-mono mb-2 z-10">STEP 0{step.s}</div>
                <div className="text-sm z-10 text-white">{step.text}</div>
              </div>
            ))}
          </div>
          <div className="mt-8 text-center bg-navy border border-teal-light p-4 rounded text-teal-light font-mono text-sm tracking-widest uppercase">
            Every transaction is publicly verifiable on-chain via Solana Devnet
          </div>
        </div>
      </div>
    </div>
  );
}
