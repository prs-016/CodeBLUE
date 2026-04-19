import { Activity, Sun, Moon } from "lucide-react";
import React, { useState } from "react";

import WarRoomGlobe from "../components/Globe/WarRoomGlobe";
import { useRegions } from "../hooks";

export default function Home() {
  const { regions } = useRegions();
  const [theme, setTheme] = useState("night");
  const critical = [...regions].sort((a, b) => (b.threshold_proximity_score || 0) - (a.threshold_proximity_score || 0))[0];

  return (
    <div className="relative h-screen w-full overflow-hidden bg-navy">
      
      {/* Background Particles (Faked via CSS/SVGs for demo, pure navy looks cleaner sometimes though) */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-grey-dark/30 via-navy to-navy pointer-events-none z-0" />

      {/* 3D GLOBE OVERLAY */}
      <div className="absolute inset-0 z-10 cursor-grab active:cursor-grabbing">
         <WarRoomGlobe regions={regions} theme={theme} />
      </div>

      {/* OVERLAY UIs */}
      <div className="pointer-events-none absolute inset-0 z-20 flex flex-col justify-between p-8 pb-12 pt-24">
        
        {/* Top Right Counter/Critical Info */}
        <div className="self-end rounded-xl border border-red-alert/50 bg-black/40 p-4 text-right shadow-[0_0_15px_rgba(192,57,43,0.3)] backdrop-blur-md">
          <div className="mb-1 flex items-center justify-end space-x-2 font-mono text-xs font-bold uppercase tracking-widest text-red-alert">
            <Activity className="h-4 w-4 animate-pulse" />
            <span>Critical Anomaly Detected</span>
          </div>
          <h2 className="mb-2 text-2xl font-bold text-white">{critical?.name || "Loading..."}</h2>
          
          <div className="text-4xl font-mono text-orange animate-pulse">
            T-{critical?.days_to_threshold || "---"} DAYS
          </div>
          <div className="text-sm text-grey-mid mt-1">UNTIL INTERVENTION WINDOW CLOSES</div>
        </div>

        {/* Bottom Title & Theme Toggle */}
        <div className="left-0 max-w-xl font-sans tracking-widest flex flex-col items-start">
           <h1 className="mb-2 text-4xl font-bold text-teal-light">THRESHOLD</h1>
           <p className="text-xl uppercase tracking-[0.2em] text-grey-mid">Climate Crisis Intelligence</p>
           
           <button 
             onClick={() => setTheme(t => t === "night" ? "day" : "night")}
             className="pointer-events-auto mt-6 flex items-center gap-2 rounded-full border border-white/20 bg-white/5 px-4 py-2 text-xs uppercase tracking-widest text-white backdrop-blur-md transition hover:bg-white/10 hover:border-white/40"
           >
             {theme === "night" ? (
               <><Sun className="w-4 h-4 text-orange" /> Switch to Day Mode</>
             ) : (
               <><Moon className="w-4 h-4 text-teal-light" /> Switch to Night Mode</>
             )}
           </button>
           <p className="mt-4 text-xs text-grey-dark mix-blend-screen">KEELING CURVE TODAY: 422.1 PPM (fallback demo reading)</p>
        </div>
      </div>
    </div>
  );
}
