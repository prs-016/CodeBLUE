import React, { useEffect, useRef, useState } from "react";
import * as THREE from "three";
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
        .bumpImageUrl("https://raw.githubusercontent.com/vasturiano/three-globe/master/example/img/earth-topology.png")
        .backgroundImageUrl("https://raw.githubusercontent.com/vasturiano/three-globe/master/example/img/night-sky.png")
        .backgroundColor("rgba(10,22,40,0)") 
        .showAtmosphere(true)
        .atmosphereColor("#0A84FF")
        .atmosphereAltitude(0.20)
        .hexPolygonResolution(3)
        .hexPolygonMargin(0.6)
        .arcDashLength(0.4)
        .arcDashGap(0.2)
        .arcDashInitialGap(() => Math.random())
        .arcDashAnimateTime(2000)
        .arcColor('color')
        .arcStroke('stroke');

      // Add the native custom Day/Night Shader Material
      const material = new THREE.ShaderMaterial({
        uniforms: {
          dayTexture: { value: new THREE.TextureLoader().load('https://raw.githubusercontent.com/vasturiano/three-globe/master/example/img/earth-blue-marble.jpg') },
          nightTexture: { value: new THREE.TextureLoader().load('https://raw.githubusercontent.com/vasturiano/three-globe/master/example/img/earth-night.jpg') },
          sunDirection: { value: new THREE.Vector3(1, 0, 0) } // Fixed sun shining from the right
        },
        vertexShader: `
          varying vec2 vUv;
          varying vec3 vNormal;
          void main() {
            vUv = uv;
            vNormal = normalize(normalMatrix * normal);
            gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
          }
        `,
        fragmentShader: `
          uniform sampler2D dayTexture;
          uniform sampler2D nightTexture;
          uniform vec3 sunDirection;

          varying vec2 vUv;
          varying vec3 vNormal;

          void main() {
            float intensity = dot(normalize(vNormal), normalize(sunDirection));
            float mixValue = smoothstep(-0.2, 0.2, intensity);
            
            vec3 dayColor = texture2D(dayTexture, vUv).rgb;
            vec3 nightColor = texture2D(nightTexture, vUv).rgb;
            
            gl_FragColor = vec4(mix(nightColor, dayColor, mixValue), 1.0);
          }
        `
      });

      globe.globeMaterial(material);

      // Add cyber-military hex grid overlay for countries
      fetch('https://raw.githubusercontent.com/vasturiano/three-globe/master/example/dataset/ne_110m_admin_0_countries.geojson')
        .then(res => res.json())
        .then(countries => {
          globe.hexPolygonsData(countries.features)
               .hexPolygonTransitionDuration(1000);
        }).catch(() => {});

      globe.pointOfView({ lat: 20, lng: 0, altitude: 2.2 });
      globe.controls().autoRotate = true;
      globe.controls().autoRotateSpeed = 1.2;

      // Click on empty globe space → trigger risk assessment pipeline
      globe.onGlobeClick(({ lat, lng }) => {
        globe.controls().autoRotate = false;
        assess(lat, lng);
      });

      globeRef.current = globe;
    }).catch(console.error);

    return () => {
      if (containerRef.current) containerRef.current.innerHTML = "";
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

    // Rings indicating active stress zones
    const ringData = regions.map((r) => ({
      lat: r.lat,
      lng: r.lon,
      maxR: Math.max(8, (r.threshold_proximity_score || 0) * 2.2),
      propagationSpeed: (r.threshold_proximity_score || 0) > 7 ? 3.5 : 1.2,
      repeatPeriod: (r.threshold_proximity_score || 0) > 7 ? 400 : 1200,
      color: getColor(r.threshold_proximity_score || 0, r.primary_threat),
      label: r.name,
      ...r,
    }));

    // Draw arcs cascading from the most critical region to all others
    const sorted = [...regions].sort((a,b) => (b.threshold_proximity_score||0) - (a.threshold_proximity_score||0));
    const critical = sorted[0];
    let arcData = [];
    if (critical && regions.length > 1) {
      arcData = regions.filter(r => r.id !== critical.id).map(r => ({
        startLat: critical.lat,
        startLng: critical.lon,
        endLat: r.lat,
        endLng: r.lon,
        color: ['rgba(230, 126, 34, 0.8)', 'rgba(20, 189, 172, 0.1)'],
        stroke: 0.3 + ((r.threshold_proximity_score||0) * 0.05)
      }));
    }

    globe
      .ringsData(ringData)
      .ringColor((d) => d.color)
      .ringMaxRadius((d) => d.maxR)
      .ringPropagationSpeed((d) => d.propagationSpeed)
      .ringRepeatPeriod((d) => d.repeatPeriod)
      .onRingHover(setHoverD)
      .onRingClick((d) => navigate(`/region/${d.id}`))
      .arcsData(arcData);
      
  }, [regions, navigate]);

  function getColor(score, threat = "thermal") {
    // Increased vibrance for colorful mode requirement
    const palette = {
      acidification: [0, 255, 204], // Vibrant cyan/teal
      thermal: score >= 8 ? [255, 51, 102] : [255, 153, 0], // Bright pink-red or hyper-orange
      hypoxia: [178, 102, 255], // Neon purple
    };
    const [r, g, b] = palette[threat] || palette.thermal;
    return (t) => `rgba(${r}, ${g}, ${b}, ${1 - t})`;
  }

  return (
    <div className="w-full h-full relative pointer-events-auto overflow-hidden">
      <div 
        ref={containerRef} 
        className="h-full w-full cursor-pointer mix-blend-screen" 
        style={{ filter: "drop-shadow(0 0 30px rgba(10,132,255,0.15))" }}
      />

      {/* Futuristic Hover Tooltip */}
      {hoverD && (
        <div
          className="absolute pointer-events-none z-50 p-5 rounded-2xl transition-all duration-300 ease-out"
          style={{
            left: "50%",
            top: "50%",
            transform: "translate(60px, -50%)",
            background: "linear-gradient(145deg, rgba(14,28,51,0.95) 0%, rgba(10,22,40,0.98) 100%)",
            border: `1px solid ${getColor(hoverD.threshold_proximity_score, hoverD.primary_threat)(0.6)}`,
            boxShadow: `0 20px 60px -10px ${getColor(hoverD.threshold_proximity_score, hoverD.primary_threat)(0.4)}, inset 0 1px 0 rgba(255,255,255,0.1)`,
            backdropFilter: "blur(12px)",
          }}
        >
          <div className="flex items-center gap-3 mb-2">
             <div 
                className="w-3 h-3 rounded-full animate-pulse" 
                style={{ backgroundColor: getColor(hoverD.threshold_proximity_score, hoverD.primary_threat)(0) }}
             />
             <h3 className="text-xl font-bold text-white tracking-wide">{hoverD.name}</h3>
          </div>
          
          <div className="grid grid-cols-2 gap-4 mt-4">
             <div className="bg-black/30 rounded-lg p-3 border border-white/5">
                <div className="text-xs text-grey-mid uppercase tracking-widest mb-1">Score</div>
                <div 
                  className="text-3xl font-mono"
                  style={{ color: getColor(hoverD.threshold_proximity_score, hoverD.primary_threat)(0) }}
                >
                  {hoverD.threshold_proximity_score.toFixed(1)}
                </div>
             </div>
             
             <div className="bg-black/30 rounded-lg p-3 border border-white/5">
                <div className="text-xs text-grey-mid uppercase tracking-widest mb-1">Threshold</div>
                <div className="text-3xl font-mono text-white">
                  T-{hoverD.days_to_threshold}
                </div>
             </div>
          </div>
          
          <div className="mt-4 text-sm text-grey-light/90 border-l-2 pl-3" style={{ borderColor: getColor(hoverD.threshold_proximity_score, hoverD.primary_threat)(0.4) }}>
             {hoverD.primary_driver}
          </div>
          <div className="mt-3 text-sm flex justify-between items-center text-grey-mid">
             <span>Estimated Gap:</span>
             <span className="text-white font-mono">${(hoverD.funding_gap / 1000000).toFixed(1)}M</span>
          </div>
          
          <div className="mt-5 w-full bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg py-2 text-center font-bold uppercase tracking-widest transition-colors cursor-pointer" style={{ color: getColor(hoverD.threshold_proximity_score, hoverD.primary_threat)(0) }}>
            Analyze Deep Threat Profile →
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
