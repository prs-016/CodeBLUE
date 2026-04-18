import { useEffect, useState, useRef } from 'react';
import { api } from '../utils/api';
import WarRoomGlobe from '../components/Globe/WarRoomGlobe';
import { Activity } from 'lucide-react';

export default function Home() {
  const [regions, setRegions] = useState([]);
  const [critical, setCritical] = useState(null);

  useEffect(() => {
    // Load regions on mount
    api.getRegions()
      .then(data => {
        setRegions(data);
        const mostCritical = data.reduce((prev, curr) => 
          (prev.threshold_proximity_score > curr.threshold_proximity_score) ? prev : curr
        );
        setCritical(mostCritical);
      })
      .catch(e => console.error("Could not fetch regions for globe", e));
  }, []);

  return (
    <div className="relative w-full h-screen bg-navy overflow-hidden">
      
      {/* Background Particles (Faked via CSS/SVGs for demo, pure navy looks cleaner sometimes though) */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-grey-dark/30 via-navy to-navy pointer-events-none z-0" />

      {/* 3D GLOBE OVERLAY */}
      <div className="absolute inset-0 z-10 cursor-grab active:cursor-grabbing">
         <WarRoomGlobe regions={regions} />
      </div>

      {/* OVERLAY UIs */}
      <div className="pointer-events-none absolute inset-0 z-20 flex flex-col justify-between p-8 pt-24 pb-12">
        
        {/* Top Right Counter/Critical Info */}
        <div className="self-end text-right bg-black/40 backdrop-blur-md border border-red-alert/50 p-4 rounded-xl shadow-[0_0_15px_rgba(192,57,43,0.3)]">
          <div className="flex items-center space-x-2 text-red-alert uppercase text-xs font-bold font-mono tracking-widest justify-end mb-1">
            <Activity className="h-4 w-4 animate-pulse" />
            <span>Critical Anomaly Detected</span>
          </div>
          <h2 className="text-2xl font-bold text-white mb-2">{critical?.name || 'Loading...'}</h2>
          
          <div className="text-4xl font-mono text-orange animate-pulse">
            T-{critical?.days_to_threshold || '---'} DAYS
          </div>
          <div className="text-sm text-grey-mid mt-1">UNTIL INTERVENTION WINDOW CLOSES</div>
        </div>

        {/* Bottom Title */}
        <div className="max-w-xl left-0 font-sans tracking-widest">
           <h1 className="text-4xl font-bold text-teal-light mb-2">THRESHOLD</h1>
           <p className="text-xl text-grey-mid uppercase tracking-[0.2em]">Climate Crisis Intelligence</p>
           <p className="text-xs text-grey-dark mt-4 mix-blend-screen">LIVE FEED ACTIVE // SECURE CONNECTION ESTABLISHED</p>
        </div>
      </div>
    </div>
  );
}
