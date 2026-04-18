import React, { useEffect, useState } from 'react';
import { api } from '../../utils/api';

export default function FundDashboard() {
  const [rounds, setRounds] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getFundingRounds().then(d => {
      setRounds(d);
      setLoading(false);
    });
  }, []);

  if (loading) return <div className="animate-pulse p-4 text-teal">Synchronizing smart contract states...</div>;

  const activeRounds = rounds.filter(r => r.status === 'Open');

  return (
    <div className="space-y-8">
      {/* Hero Stats */}
      <div className="grid grid-cols-3 gap-6">
        <div className="bg-grey-dark/20 p-6 rounded-xl border border-grey-dark">
          <div className="text-grey-mid uppercase text-xs tracking-widest font-bold mb-2">Total Deployed via THRESHOLD</div>
          <div className="text-3xl font-mono text-white">$15.4M</div>
        </div>
        <div className="bg-grey-dark/20 p-6 rounded-xl border border-grey-dark">
          <div className="text-grey-mid uppercase text-xs tracking-widest font-bold mb-2">Active Rounds Triggered</div>
          <div className="text-3xl font-mono text-white">{activeRounds.length}</div>
        </div>
        <div className="bg-teal/10 p-6 rounded-xl border border-teal/30">
          <div className="text-teal-light uppercase text-xs tracking-widest font-bold mb-2">Measured Impact (Avg Score Delta)</div>
          <div className="text-3xl font-mono text-teal-light">↓ -2.4 points</div>
        </div>
      </div>

      <h2 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-red-alert to-orange ml-4 pt-4">
        Active Emergency Funding Rounds
      </h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {activeRounds.map(r => (
          <div key={r.id} className="bg-navy border border-red-alert/40 rounded-xl overflow-hidden shadow-2xl relative flex flex-col">
            <div className="absolute top-0 w-full h-1 bg-gradient-to-r from-red-alert to-orange"></div>
            <div className="p-6 flex-grow">
              <div className="flex justify-between items-start mb-4">
                 <div>
                   <h3 className="font-bold text-lg">{r.region_name}</h3>
                   <span className="text-xs text-red-alert border border-red-alert px-2 py-0.5 rounded uppercase tracking-widest">
                     {r.threat_type} Warning
                   </span>
                 </div>
                 <div className="bg-orange/20 text-orange font-mono font-bold text-sm px-2 py-1 rounded">
                   1$ → {r.cost_multiplier}X
                 </div>
              </div>
              
              <div className="mb-4">
                 <div className="flex justify-between text-xs font-mono text-grey-mid mb-1">
                   <span>${(r.raised_amount / 1000).toFixed(0)}k raised</span>
                   <span>${(r.target_amount / 1000).toFixed(0)}k target</span>
                 </div>
                 <div className="w-full bg-grey-dark rounded-full h-2 overflow-hidden">
                   <div 
                     className="bg-teal-light h-full" 
                     style={{width: `${(r.raised_amount / r.target_amount)*100}%`}}
                   />
                 </div>
              </div>
              
              <div className="text-sm font-mono text-orange mb-6">
                Ends {r.deadline}
              </div>
            </div>
            
            <button className="w-full bg-teal hover:bg-teal-light text-navy font-bold uppercase tracking-widest transform transition-all py-4">
               Contribute via Smart Contract
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
