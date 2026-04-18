import React, { useEffect, useRef, useState } from 'react';
import Globe from 'globe.gl';
import { useNavigate } from 'react-router-dom';
import * as d3 from 'd3';

export default function WarRoomGlobe({ regions }) {
  const globeRef = useRef();
  const containerRef = useRef();
  const navigate = useNavigate();
  const [hoverD, setHoverD] = useState(null);

  useEffect(() => {
    if (!containerRef.current) return;

    // Initialize Globe
    const globe = Globe()(containerRef.current)
      .globeImageUrl('//unpkg.com/three-globe/example/img/earth-dark.jpg') // Dark base layer
      .backgroundColor('#0A1628') // Match --navy
      .showAtmosphere(true)
      .atmosphereColor('#14BDAC')
      .atmosphereAltitude(0.15);

    // Default point of view
    globe.pointOfView({ lat: 20, lng: 0, altitude: 2.5 });

    // Controls
    globe.controls().autoRotate = true;
    globe.controls().autoRotateSpeed = 0.5;

    globeRef.current = globe;

    // Cleanup
    return () => {
      // remove the globe to prevent memory leaks on unmount if needed
      containerRef.current.innerHTML = '';
    };
  }, []);

  // Update Data dynamically
  useEffect(() => {
    if (!globeRef.current || !regions || regions.length === 0) return;

    const globe = globeRef.current;

    // Map regions into rings/polygons to show heat spots
    // For demo simplicity using rings
    const ringData = regions.map(r => ({
      lat: r.lat,
      lng: r.lon,
      maxR: Math.max(5, (r.threshold_proximity_score || 0) * 1.5), // size based on score
      propagationSpeed: (r.threshold_proximity_score || 0) > 7 ? 2.5 : 1, // pulse faster if critical
      repeatPeriod: (r.threshold_proximity_score || 0) > 7 ? 600 : 1500,
      color: getColor(r.threshold_proximity_score || 0),
      label: r.name,
      ...r
    }));

    globe
      .ringsData(ringData)
      .ringColor(d => d.color)
      .ringMaxRadius(d => d.maxR)
      .ringPropagationSpeed(d => d.propagationSpeed)
      .ringRepeatPeriod(d => d.repeatPeriod)
      .onRingHover(setHoverD)
      .onRingClick(d => navigate(`/region/${d.id}`));

    // Draw lines/labels if desired, but rings alone with tooltips look stunning
  }, [regions, navigate]);

  function getColor(score) {
    if (score >= 8) return t => `rgba(192, 57, 43, ${1 - t})`;  // Red
    if (score >= 6) return t => `rgba(230, 126, 34, ${1 - t})`; // Orange 
    if (score >= 4) return t => `rgba(241, 196, 15, ${1 - t})`; // Yellow
    return t => `rgba(13, 115, 119, ${1 - t})`;               // Teal
  }

  return (
    <div className="w-full h-full relative pointer-events-auto">
      <div ref={containerRef} className="w-full h-full cursor-pointer" />
      {/* Tooltip Overlay */}
      {hoverD && (
        <div className="absolute pointer-events-none z-50 bg-navy/90 border border-grey-dark p-4 rounded shadow-2xl backdrop-blur-sm"
             style={{ 
                left: '50%', top: '50%', transform: 'translate(40px, -50%)', 
                boxShadow: `0 0 20px ${getColor(hoverD.threshold_proximity_score)(0.5)}` 
             }}>
          <h3 className="text-lg font-bold text-white mb-1">{hoverD.name}</h3>
          <div className="text-3xl font-mono mb-2" style={{ color: getColor(hoverD.threshold_proximity_score)(0) }}>
            {hoverD.threshold_proximity_score.toFixed(1)} <span className="text-sm font-sans text-grey-mid">SCORE</span>
          </div>
          <div className="text-sm text-grey-mid">
            T-{hoverD.days_to_threshold} Days to Threshold
          </div>
          <div className="text-sm text-grey-mid mt-1">
             Gap: ${(hoverD.funding_gap / 1000000).toFixed(1)}M
          </div>
          <div className="text-teal-light text-xs font-bold mt-3 uppercase tracking-widest">
            Click to View Brief →
          </div>
        </div>
      )}
    </div>
  );
}
