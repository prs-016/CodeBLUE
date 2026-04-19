import React, { useEffect, useState } from 'react';
import { api } from '../../utils/api';
import TriageRow from './TriageRow';

export default function TriageQueue() {
  const [regions, setRegions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getTriage('sort_by=days_to_threshold&order=asc')
      .then(data => {
        setRegions(data);
        setLoading(false);
      })
      .catch(e => {
        console.error(e);
        setLoading(false);
      });
  }, []);

  if (loading) return <div className="text-teal animate-pulse">Loading intelligence feed...</div>;

  return (
    <div className="bg-navy border border-grey-dark rounded-xl overflow-hidden shadow-2xl">
      <div className="flex justify-between items-center bg-grey-dark/30 p-4 border-b border-grey-dark">
        <div className="flex space-x-4 text-sm">
          <select className="bg-navy border border-grey-dark text-white rounded px-2 py-1 outline-none">
            <option>All Threats</option>
            <option>Thermal</option>
            <option>Hypoxia</option>
          </select>
          <div className="text-grey-mid py-1 px-2">{regions.length} Regions</div>
        </div>
        <button className="bg-teal/20 text-teal-light px-4 py-1 rounded hover:bg-teal/40 transition">
          Export CSV
        </button>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-navy text-grey-mid text-xs uppercase tracking-wider border-b border-grey-dark">
              <th className="p-4 font-medium">Region</th>
              <th className="p-4 font-medium">Threat</th>
              <th className="p-4 font-medium">Days to Threshold</th>
              <th className="p-4 font-medium w-48">Proximity Score</th>
              <th className="p-4 font-medium text-right">Committed / Gap</th>
              <th className="p-4 font-medium text-center">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-grey-dark/50">
            {regions.map(r => (
              <TriageRow key={r.id} region={r} />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
