import React from 'react';
import { useNavigate } from 'react-router-dom';

export default function TriageRow({ region }) {
  const navigate = useNavigate();

  const getThreatColor = (t) => {
    switch (t) {
      case 'thermal': return 'bg-red-alert/20 text-red-alert border-red-alert/50';
      case 'hypoxia': return 'bg-orange/20 text-orange border-orange/50';
      case 'acidification': return 'bg-yellow/20 text-yellow border-yellow/50';
      case 'nutrient': return 'bg-teal/20 text-teal-light border-teal/50';
      default: return 'bg-grey-dark text-white border-grey-mid';
    }
  };

  const getUrgencyColor = (score) => {
    if (score >= 8) return 'bg-red-alert';
    if (score >= 6) return 'bg-orange';
    if (score >= 4) return 'bg-yellow';
    return 'bg-teal';
  };

  return (
    <tr className="hover:bg-grey-dark/20 transition-colors group">
      <td className="p-4 font-medium text-white">{region.name}</td>
      <td className="p-4">
        <span className={`px-2 py-1 text-xs rounded border ${getThreatColor(region.threat_type)} uppercase tracking-widest`}>
          {region.threat_type}
        </span>
      </td>
      <td className="p-4">
        <div className={`text-xl font-mono font-bold ${region.days_to_threshold < 90 ? 'text-red-alert' : 'text-white'}`}>
          {region.days_to_threshold} <span className="text-sm font-sans tracking-tight text-grey-mid font-normal">DAYS</span>
        </div>
      </td>
      <td className="p-4 w-48">
        <div className="flex items-center justify-between mb-1">
          <span className="text-xs font-mono">{region.current_score.toFixed(1)}/10</span>
        </div>
        <div className="w-full bg-grey-dark rounded-full h-1.5 overflow-hidden">
          <div 
            className={`h-full ${getUrgencyColor(region.current_score)}`} 
            style={{ width: `${(region.current_score / 10) * 100}%` }}
          />
        </div>
      </td>
      <td className="p-4 text-right">
        <div className="text-sm font-mono text-grey-light mb-1">
          Total Gap
        </div>
        <div className="text-red-alert font-mono text-sm">
          ${(region.funding_gap / 1000000).toFixed(1)}M
        </div>
      </td>
      <td className="p-4 text-center">
        <button 
          onClick={() => navigate(`/region/${region.id}`)}
          className="text-teal-light opacity-0 group-hover:opacity-100 transition duration-300 font-bold uppercase text-xs tracking-wider"
        >
          View Brief →
        </button>
      </td>
    </tr>
  );
}
