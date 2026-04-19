import React, { useEffect, useRef, useState, useMemo, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useTsunamis } from "../../hooks";

export default function WarRoomGlobe({ regions, onAssess }) {
  const globeRef    = useRef(null);
  const containerRef = useRef(null);
  const navigate    = useNavigate();
  const { tsunamis } = useTsunamis();
  const [currentYear, setCurrentYear] = useState(null);

  // Stable refs — handlers inside the one-time globe init always see latest values
  const onAssessRef  = useRef(onAssess);
  const navigateRef  = useRef(navigate);
  useEffect(() => { onAssessRef.current  = onAssess;  }, [onAssess]);
  useEffect(() => { navigateRef.current  = navigate;  }, [navigate]);

  // Latest data ref — init callback reads this after globe is created
  const dataRef = useRef({ regionRings: [], tsunamis: [], currentYear: null });

  // ── Year animation ────────────────────────────────────────────────────────
  useEffect(() => {
    if (!tsunamis?.length || currentYear !== null) return;
    const years = tsunamis.map(t => t.year).filter(y => y != null && y >= 1900);
    if (years.length) setCurrentYear(Math.min(...years));
  }, [tsunamis, currentYear]);

  useEffect(() => {
    if (currentYear === null || !tsunamis?.length) return;
    const id = setInterval(() => {
      setCurrentYear(prev => {
        const next = prev + 1;
        const max  = new Date().getFullYear();
        if (next > max) {
          const years = tsunamis.map(t => t.year).filter(y => y != null && y >= 1900);
          return Math.min(...years);
        }
        return next;
      });
    }, 140);
    return () => clearInterval(id);
  }, [currentYear, tsunamis]);


  // ── Ring data computation ─────────────────────────────────────────────────
  const regionRings = useMemo(() => (regions || []).map(r => {
    const score      = r.threshold_proximity_score || 0;
    const isCritical = score >= 7;
    return {
      ...r,
      lat: Number(r.lat),
      lng: Number(r.lon),
      maxR: Math.max(6, score * 2.4),
      propagationSpeed: isCritical ? 4 : 1.5,
      repeatPeriod:     isCritical ? 350 : 1100,
      color: ringColorFn(score, r.primary_threat),
      isTsunami: false,
    };
  }), [regions]);

  const allTsunamiRings = useMemo(() => (tsunamis || [])
    .filter(t => t.lat != null && t.lng != null && t.year != null)
    .map(t => ({
      ...t,
      lat: Number(t.lat),
      lng: Number(t.lng),
      maxR: Math.max(3, (t.magnitude || 5) * 1.6),
      propagationSpeed: 6,
      repeatPeriod: 200,
      color: (tt) => `rgba(0,210,255,${1 - tt})`,
      isTsunami: true,
    })), [tsunamis]);

  // ── Core function: push current data into the globe instance ─────────────
  const pushData = useCallback((globe) => {
    if (!globe) return;
    const { regionRings: rr, tsunamis: allT, currentYear: cy } = dataRef.current;

    const activeTsunamis = cy !== null
      ? allT.filter(t => Math.abs(t.year - cy) <= 1).map(t => ({
          ...t,
          color: (tt) => `rgba(0,210,255,${(1 - tt) * (t.year === cy ? 1 : 0.5)})`,
        }))
      : [];

    // Expand regions with score >= 4 into a cluster of 7 red rings!
    // The center ring + 6 immediate neighbors to form that intense localized cluster.
    const clusterRings = [];
    rr.forEach(r => {
      const score = r.threshold_proximity_score || 0;
      if (score >= 4) {
        // Center ring (solid red, high propagation speed)
        clusterRings.push({ ...r, color: (t) => `rgba(255,0,0,${1 - t})`, maxR: r.maxR });
        
        // 6 immediate neighbors to form the surrounding cluster inside a circle
        const d = 1.6; // distance in degrees
        const lngScale = Math.cos(r.lat * Math.PI / 180) || 1;
        for (let i = 0; i < 6; i++) {
          const angle = (Math.PI / 3) * i;
          clusterRings.push({
            lat: r.lat + d * Math.sin(angle),
            lng: r.lng + (d * Math.cos(angle)) / lngScale,
            maxR: r.maxR * 0.75, // slightly smaller neighbor rings
            propagationSpeed: r.propagationSpeed * 0.9,
            repeatPeriod: r.repeatPeriod,
            color: (t) => `rgba(255,0,0,${0.8 - t})` // intensely red
          });
        }
      } else {
        // Keep normal styling for low severity
        clusterRings.push(r);
      }
    });

    globe.ringsData([...clusterRings, ...activeTsunamis]);

    // Arcs: most critical → all others
    const sorted = [...rr].sort(
      (a, b) => (b.threshold_proximity_score || 0) - (a.threshold_proximity_score || 0)
    );
    const top = sorted[0];
    const arcs = top && sorted.length > 1
      ? sorted.slice(1).map(r => ({
          startLat: top.lat, startLng: top.lng,
          endLat: r.lat, endLng: r.lng,
          color: ["rgba(230,126,34,0.7)", "rgba(20,189,172,0.08)"],
          stroke: 0.25 + (r.threshold_proximity_score || 0) * 0.04,
        }))
      : [];
    globe.arcsData(arcs);

    // Labels only for high-risk regions
    globe.labelsData(rr.filter(r => (r.threshold_proximity_score || 0) >= 5));
  }, []);

  // ── Keep data ref in sync, then push to globe ─────────────────────────────
  useEffect(() => {
    dataRef.current = { regionRings, tsunamis: allTsunamiRings, currentYear };
    pushData(globeRef.current);
  }, [regionRings, allTsunamiRings, currentYear, pushData]);

  // ── Globe initialisation (once) ───────────────────────────────────────────
  useEffect(() => {
    if (!containerRef.current) return;
    let cancelled = false;

    import("globe.gl").then(pkg => {
      if (cancelled || !containerRef.current) return;
      const Globe = pkg.default || pkg;

      const globe = Globe()(containerRef.current)
        .globeImageUrl("https://raw.githubusercontent.com/vasturiano/three-globe/master/example/img/earth-blue-marble.jpg")
        .bumpImageUrl("https://raw.githubusercontent.com/vasturiano/three-globe/master/example/img/earth-topology.png")
        .backgroundImageUrl("https://raw.githubusercontent.com/vasturiano/three-globe/master/example/img/night-sky.png")
        .backgroundColor("rgba(7,14,26,1)")
        .showAtmosphere(true)
        .atmosphereColor("#1a6ebd")
        .atmosphereAltitude(0.20)
        // Hex grid
        .hexPolygonResolution(3)
        .hexPolygonMargin(0.62)
        .hexPolygonColor(() => "rgba(20, 189, 172, 0.15)") // Cool dim teal for normal countries
        // Arcs
        .arcDashLength(0.35)
        .arcDashGap(0.15)
        .arcDashInitialGap(() => Math.random())
        .arcDashAnimateTime(1800)
        .arcColor("color")
        .arcStroke("stroke")
        // Rings — accessors + defaults
        .ringLat("lat")
        .ringLng("lng")
        .ringColor("color")
        .ringMaxRadius("maxR")
        .ringPropagationSpeed("propagationSpeed")
        .ringRepeatPeriod("repeatPeriod")
        // Labels
        .labelLat("lat")
        .labelLng("lng")
        .labelText("name")
        .labelSize(0.5)
        .labelColor(() => "rgba(255,255,255,0.9)")
        .labelDotRadius(0)
        .labelResolution(2)
        // Events — onRingHover/onRingClick don't exist in globe.gl 2.x
        // Globe click for risk assessment
        .onGlobeClick(({ lat, lng }) => {
          globe.controls().autoRotate = false;
          onAssessRef.current?.(lat, lng);
        });

      globe.pointOfView({ lat: 20, lng: 10, altitude: 2.1 });
      globe.controls().autoRotate      = true;
      globe.controls().autoRotateSpeed = 0.9;
      globe.controls().enableDamping   = true;

      // Country hex grid overlay
      fetch("https://raw.githubusercontent.com/vasturiano/globe.gl/master/example/datasets/ne_110m_admin_0_countries.geojson")
        .then(r => r.json())
        .then(geo => { if (!cancelled) globe.hexPolygonsData(geo.features).hexPolygonTransitionDuration(1000); })
        .catch(() => {});

      globeRef.current = globe;

      // Push whatever data is already loaded
      pushData(globe);
    }).catch(err => {
      console.error("Globe init error:", err);
      if (document.body) document.body.innerHTML += '<div style="position:absolute;z-index:9999;color:red;background:black;padding:10px;top:0;">Globe Error: ' + err.message + '</div>';
    });

    return () => {
      cancelled = true;
      globeRef.current = null;
      if (containerRef.current) containerRef.current.innerHTML = "";
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="relative h-full w-full overflow-hidden">
      <div
        ref={containerRef}
        className="h-full w-full"
      />

      {/* Year overlay removed — user preference */}
    </div>
  );
}

// ── Color helpers ─────────────────────────────────────────────────────────────
function ringColorFn(score, threat = "thermal") {
  // User requested anything moderate/high (not low) to light up bright red
  if (score >= 4) return (t) => `rgba(255,0,0,${1 - t})`;

  // Low severity fallback colors
  if (threat === "acidification") return (t) => `rgba(0,230,200,${1 - t})`;
  if (threat === "hypoxia")       return (t) => `rgba(170,90,255,${1 - t})`;
  return                                 (t) => `rgba(20,180,170,${1 - t})`;
}

