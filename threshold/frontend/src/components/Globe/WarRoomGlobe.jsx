import React, { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import RiskCard from "../RiskCard/RiskCard";
import { useRiskAssessment } from "../../hooks/useRiskAssessment";

export default function WarRoomGlobe({ regions }) {
  const globeRef = useRef();
  const containerRef = useRef();
  const navigate = useNavigate();
  const [hoverD, setHoverD] = useState(null);
  const { quick, enrich, loadingQuick, loadingEnrich, assess, clear } = useRiskAssessment();

  useEffect(() => {
    if (!containerRef.current) return;
    import("globe.gl").then((GlobePkg) => {
      const Globe = GlobePkg.default || GlobePkg;

      const globe = Globe()(containerRef.current)
        .globeImageUrl("//unpkg.com/three-globe/example/img/earth-dark.jpg")
        .backgroundColor("#0A1628")
        .showAtmosphere(true)
        .atmosphereColor("#14BDAC")
        .atmosphereAltitude(0.15);

      globe.pointOfView({ lat: 20, lng: 0, altitude: 2.5 });
      globe.controls().autoRotate = true;
      globe.controls().autoRotateSpeed = 0.5;

      // Click on empty globe space → trigger risk assessment pipeline
      globe.onGlobeClick(({ lat, lng }) => {
        globe.controls().autoRotate = false;
        assess(lat, lng);
      });

      globeRef.current = globe;
    }).catch(console.error);

    return () => {
      containerRef.current.innerHTML = "";
    };
  }, []);

  // Separate effect so assess reference doesn't recreate the globe
  useEffect(() => {
    if (!globeRef.current) return;
    globeRef.current.onGlobeClick(({ lat, lng }) => {
      globeRef.current.controls().autoRotate = false;
      assess(lat, lng);
    });
  }, [assess]);

  useEffect(() => {
    if (!globeRef.current || !regions || regions.length === 0) return;
    const globe = globeRef.current;

    const ringData = regions.map((r) => ({
      lat: r.lat,
      lng: r.lon,
      maxR: Math.max(5, (r.threshold_proximity_score || 0) * 1.5),
      propagationSpeed: (r.threshold_proximity_score || 0) > 7 ? 2.5 : 1,
      repeatPeriod: (r.threshold_proximity_score || 0) > 7 ? 600 : 1500,
      color: getColor(r.threshold_proximity_score || 0),
      label: r.name,
      ...r,
    }));

    globe
      .ringsData(ringData)
      .ringColor((d) => d.color)
      .ringMaxRadius((d) => d.maxR)
      .ringPropagationSpeed((d) => d.propagationSpeed)
      .ringRepeatPeriod((d) => d.repeatPeriod)
      .onRingHover(setHoverD)
      .onRingClick((d) => navigate(`/region/${d.id}`));
  }, [regions, navigate]);

  function getColor(score, threat = "thermal") {
    const palette = {
      acidification: [26, 163, 184],
      thermal: score >= 8 ? [192, 57, 43] : [230, 126, 34],
      hypoxia: [126, 87, 194],
    };
    const [r, g, b] = palette[threat] || palette.thermal;
    return (t) => `rgba(${r}, ${g}, ${b}, ${1 - t})`;
  }

  return (
    <div className="w-full h-full relative pointer-events-auto">
      <div ref={containerRef} className="h-full w-full cursor-pointer" />

      {/* Existing region hover tooltip */}
      {hoverD && (
        <div
          className="absolute pointer-events-none z-50 bg-navy/90 border border-grey-dark p-4 rounded shadow-2xl backdrop-blur-sm"
          style={{
            left: "50%",
            top: "50%",
            transform: "translate(40px, -50%)",
            boxShadow: `0 0 20px ${getColor(hoverD.threshold_proximity_score, hoverD.primary_threat)(0.5)}`,
          }}
        >
          <h3 className="text-lg font-bold text-white mb-1">{hoverD.name}</h3>
          <div
            className="text-3xl font-mono mb-2"
            style={{ color: getColor(hoverD.threshold_proximity_score, hoverD.primary_threat)(0) }}
          >
            {hoverD.threshold_proximity_score.toFixed(1)}{" "}
            <span className="text-sm font-sans text-grey-mid">SCORE</span>
          </div>
          <div className="text-sm text-grey-mid">T-{hoverD.days_to_threshold} Days to Threshold</div>
          <div className="mt-1 text-sm text-white">{hoverD.primary_driver}</div>
          <div className="text-sm text-grey-mid mt-1">Gap: ${(hoverD.funding_gap / 1000000).toFixed(1)}M</div>
          <div className="text-teal-light text-xs font-bold mt-3 uppercase tracking-widest">
            Click to View Brief →
          </div>
        </div>
      )}

      {/* Risk assessment card — shown on arbitrary globe click */}
      {(loadingQuick || quick) && (
        <RiskCard
          quick={quick}
          enrich={enrich}
          loadingQuick={loadingQuick}
          loadingEnrich={loadingEnrich}
          onClose={() => {
            clear();
            if (globeRef.current) globeRef.current.controls().autoRotate = true;
          }}
        />
      )}
    </div>
  );
}
