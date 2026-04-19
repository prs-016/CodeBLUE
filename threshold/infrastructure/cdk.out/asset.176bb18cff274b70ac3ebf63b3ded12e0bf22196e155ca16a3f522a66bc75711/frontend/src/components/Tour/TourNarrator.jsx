import React, { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

const API_BASE =
  (typeof import.meta !== "undefined" && import.meta?.env?.VITE_API_URL) ||
  "http://localhost:8000";
const TOUR_KEY = "threshold_tour_v2";

// ── Tour step definitions ─────────────────────────────────────────────────────
// indicator: where the glowing pulse appears (null = no spotlight)
// card: where the explanation card is anchored
const STEPS = [
  {
    route: "/",
    title: "War Room Globe",
    subtitle: "Step 1 — Home",
    emoji: "🌍",
    indicator: null,
    card: "center",
    description:
      "This 3D globe shows eight of Earth's most threatened marine ecosystems in real time. Each pulsing ring is a region approaching ecological collapse — color shifts from teal to red as crisis deepens.",
  },
  {
    route: "/",
    title: "Critical Anomaly Badge",
    subtitle: "Step 2 — Home",
    emoji: "🚨",
    indicator: { top: "88px", right: "28px" },
    card: "left",
    description:
      "Tracks the most endangered ecosystem globally. The T-minus counter counts down to the point of no return — when recovery costs multiply by up to 14×.",
  },
  {
    route: "/",
    title: "Live Data Feeds",
    subtitle: "Step 3 — Home",
    emoji: "📡",
    indicator: { bottom: "38px", left: "28px" },
    card: "right",
    description:
      "Every score is powered by real data: CalCOFI ocean sensors from Scripps Institution of Oceanography, GDELT conflict events from Snowflake, and Gemini AI for grounded news.",
  },
  {
    route: "/triage",
    title: "Triage Queue",
    subtitle: "Step 4 — Triage",
    emoji: "⚡",
    indicator: { top: "160px", left: "50%", transform: "translateX(-50%)" },
    card: "center",
    description:
      "Every monitored region ranked by urgency. ThresholdNet — our bidirectional LSTM neural network — scores each ecosystem 0–10 against IPCC, NOAA, and EPA thresholds. Most critical regions rise to the top.",
  },
  {
    route: "/region/great_barrier_reef",
    title: "Region Intelligence Brief",
    subtitle: "Step 5 — Region",
    emoji: "🔬",
    indicator: null,
    card: "center",
    description:
      "Full intelligence dossier per ecosystem: live stress signals, dissolved oxygen curves, sea temperature anomalies, funding gap analysis, and branching intervention scenarios modeled from historical cases.",
  },
  {
    route: "/counterfactual",
    title: "Counterfactual Engine",
    subtitle: "Step 6 — Counterfactual",
    emoji: "⏱",
    indicator: { top: "50%", left: "50%", transform: "translate(-50%,-50%)" },
    card: "bottom",
    description:
      "What would it have cost if we acted sooner? Drag the timeline scrubber to explore intervention windows. The cost divergence is dramatic — and it's always the same story.",
  },
  {
    route: "/funding-gap",
    title: "Funding Gap Radar",
    subtitle: "Step 7 — Funding Gap",
    emoji: "📊",
    indicator: { top: "50%", left: "50%", transform: "translate(-50%,-50%)" },
    card: "bottom",
    description:
      "Regions in the bottom-right quadrant have critical scores and almost no committed capital. These are the blind spots where ecosystems collapse without headlines.",
  },
  {
    route: "/fund",
    title: "Threshold Fund",
    subtitle: "Step 8 — Fund",
    emoji: "⛓",
    indicator: { top: "160px", left: "50%", transform: "translateX(-50%)" },
    card: "center",
    description:
      "Donate by card — we write an immutable Solana blockchain record on your behalf. Publicly verifiable by anyone. No crypto wallet required. This is transparent climate finance.",
  },
];

// Waveform bars
const BAR_COUNT = 14;
const waveCSS = `
@keyframes tourWave {
  0%   { height: 3px;  opacity: 0.35; }
  100% { height: 18px; opacity: 0.9;  }
}
@keyframes tourPulse {
  0%, 100% { transform: scale(1);   opacity: 0.9; }
  50%       { transform: scale(1.6); opacity: 0.3; }
}
@keyframes tourFadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0);   }
}
`;

export default function TourNarrator() {
  const navigate = useNavigate();
  const [visible, setVisible]     = useState(() => !sessionStorage.getItem(TOUR_KEY));
  const [started, setStarted]     = useState(false);
  const [stepIdx, setStepIdx]     = useState(0);
  const [audioState, setAudioState] = useState("idle"); // idle|loading|playing|paused|error
  const [progress, setProgress]   = useState(0);
  const [errorMsg, setErrorMsg]   = useState(null);
  const audioRef  = useRef(null);
  const blobUrls  = useRef({}); // cache blob URLs per step

  // Inject CSS once
  useEffect(() => {
    if (document.getElementById("tour-css")) return;
    const s = document.createElement("style");
    s.id = "tour-css";
    s.textContent = waveCSS;
    document.head.appendChild(s);
  }, []);

  // Listen for navbar "▶ Tour" button
  useEffect(() => {
    const handler = () => {
      audioRef.current?.pause();
      sessionStorage.removeItem(TOUR_KEY);
      setStepIdx(0);
      setStarted(false);
      setAudioState("idle");
      setProgress(0);
      setErrorMsg(null);
      setVisible(true);
    };
    window.addEventListener("restart-tour", handler);
    return () => window.removeEventListener("restart-tour", handler);
  }, []);

  const step = STEPS[stepIdx];
  const isLast = stepIdx === STEPS.length - 1;

  // Navigate whenever step changes (after tour started)
  useEffect(() => {
    if (started) navigate(step.route);
  }, [stepIdx, started]); // eslint-disable-line

  // Pre-fetch current step audio (and next step in background)
  const fetchAudio = useCallback(async (idx) => {
    if (blobUrls.current[idx]) return blobUrls.current[idx];
    const resp = await fetch(`${API_BASE}/api/v1/tour/narration?step=${idx}`);
    if (!resp.ok) {
      const body = await resp.json().catch(() => ({}));
      throw new Error(body?.detail || `HTTP ${resp.status}`);
    }
    const blob = await resp.blob();
    const url = URL.createObjectURL(blob);
    blobUrls.current[idx] = url;
    return url;
  }, []);

  // Play audio for a given step
  const playStep = useCallback(async (idx) => {
    setAudioState("loading");
    setErrorMsg(null);
    setProgress(0);
    try {
      const url = await fetchAudio(idx);
      // Pre-fetch next step silently
      if (idx + 1 < STEPS.length) fetchAudio(idx + 1).catch(() => {});

      const audio = audioRef.current;
      audio.src = url;
      audio.load();
      await audio.play();
      setAudioState("playing");
    } catch (err) {
      setErrorMsg(err.message);
      setAudioState("error");
    }
  }, [fetchAudio]);

  // Wire audio element events
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;
    const onTime   = () => setProgress(audio.duration ? audio.currentTime / audio.duration : 0);
    const onEnded  = () => setAudioState("idle");
    const onPause  = () => setAudioState(a => a === "playing" ? "paused" : a);
    const onPlay   = () => setAudioState("playing");
    audio.addEventListener("timeupdate",    onTime);
    audio.addEventListener("ended",         onEnded);
    audio.addEventListener("pause",         onPause);
    audio.addEventListener("play",          onPlay);
    return () => {
      audio.removeEventListener("timeupdate",    onTime);
      audio.removeEventListener("ended",         onEnded);
      audio.removeEventListener("pause",         onPause);
      audio.removeEventListener("play",          onPlay);
    };
  }, []);

  function startTour() {
    setStarted(true);
    navigate(STEPS[0].route);
    playStep(0);
  }

  function goTo(idx) {
    audioRef.current?.pause();
    setStepIdx(idx);
    playStep(idx);
  }

  function handleNext() {
    if (isLast) return endTour();
    goTo(stepIdx + 1);
  }

  function handlePrev() {
    if (stepIdx === 0) return;
    goTo(stepIdx - 1);
  }

  function togglePause() {
    const audio = audioRef.current;
    if (!audio) return;
    if (audio.paused) audio.play();
    else audio.pause();
  }

  function endTour() {
    audioRef.current?.pause();
    sessionStorage.setItem(TOUR_KEY, "1");
    setVisible(false);
    Object.values(blobUrls.current).forEach(URL.revokeObjectURL);
  }

  if (!visible) return (
    <audio ref={audioRef} style={{ display: "none" }} />
  );

  const isPlaying = audioState === "playing";

  return (
    <>
      <audio ref={audioRef} style={{ display: "none" }} />

      {/* ── Compact bottom-right mini-player — never covers page content ── */}
      <div
        className="fixed bottom-5 right-5 z-[500] pointer-events-auto"
        style={{ width: "min(280px, calc(100vw - 40px))", animation: "tourFadeIn 0.3s ease" }}
        key={`tour-${started}-${stepIdx}`}
      >
        <div className="rounded-2xl border border-white/12 bg-[#050c18]/95 shadow-[0_8px_32px_rgba(0,0,0,0.7)] backdrop-blur-xl overflow-hidden">
          {/* Colour accent bar */}
          <div className="h-[2px] bg-gradient-to-r from-teal-light/0 via-teal-light to-orange/60" />

          <div className="px-3 py-2.5">
            {!started ? (
              /* ── Intro prompt ── */
              <div className="flex items-center gap-3">
                <div className="flex-1 min-w-0">
                  <div className="font-mono text-[9px] uppercase tracking-[0.22em] text-teal-light">
                    Guided Tour · AI Voice
                  </div>
                  <div className="text-xs font-bold text-white truncate">War Room Briefing</div>
                </div>
                <button
                  onClick={startTour}
                  className="shrink-0 rounded-lg bg-teal-light px-3 py-1.5 text-[11px] font-bold uppercase tracking-[0.15em] text-navy hover:brightness-110 transition-all"
                >
                  ▶ Start
                </button>
                <button
                  onClick={endTour}
                  className="shrink-0 text-grey-dark hover:text-grey-mid transition-colors text-lg leading-none"
                >
                  ×
                </button>
              </div>
            ) : (
              /* ── Active step ── */
              <div className="space-y-2">
                {/* Title row */}
                <div className="flex items-center gap-2">
                  <span className="text-base leading-none">{step.emoji}</span>
                  <div className="flex-1 min-w-0">
                    <div className="font-mono text-[9px] text-grey-dark uppercase tracking-[0.2em]">{step.subtitle}</div>
                    <div className="text-xs font-bold text-white truncate">{step.title}</div>
                  </div>
                  <button onClick={endTour} className="shrink-0 text-grey-dark hover:text-grey-mid text-lg leading-none transition-colors">×</button>
                </div>

                {/* Description — single line truncated, tap to expand not needed */}
                <p className="text-[10px] text-grey-mid leading-relaxed line-clamp-2">
                  {step.description}
                </p>

                {/* Progress dots */}
                <div className="flex items-center gap-1">
                  {STEPS.map((_, i) => (
                    <button
                      key={i}
                      onClick={() => goTo(i)}
                      className={`h-1 rounded-full transition-all duration-300 ${
                        i === stepIdx ? "w-4 bg-teal-light" : i < stepIdx ? "w-1 bg-teal-light/40" : "w-1 bg-white/15"
                      }`}
                    />
                  ))}
                  <span className="ml-auto font-mono text-[9px] text-grey-dark">{stepIdx + 1}/{STEPS.length}</span>
                </div>

                {/* Audio row */}
                <div className="flex items-center gap-2 h-5">
                  {audioState === "loading" && (
                    <span className="font-mono text-[9px] text-grey-dark animate-pulse flex-1">Generating voice…</span>
                  )}
                  {audioState === "error" && (
                    <span className="font-mono text-[9px] text-red-400 truncate flex-1">{errorMsg}</span>
                  )}
                  {(isPlaying || audioState === "paused") && (
                    <>
                      <div className="flex items-end gap-[2px] shrink-0">
                        {Array.from({ length: BAR_COUNT }).map((_, i) => (
                          <div
                            key={i}
                            style={{
                              width: "2px", borderRadius: "1px",
                              background: "rgba(20,189,172,0.8)",
                              height: isPlaying ? undefined : "3px",
                              alignSelf: "center",
                              animation: isPlaying
                                ? `tourWave ${0.5 + (i % 4) * 0.11}s ease-in-out ${(i * 0.055).toFixed(2)}s infinite alternate`
                                : "none",
                            }}
                          />
                        ))}
                      </div>
                      <div className="flex-1 h-0.5 rounded-full bg-white/10 overflow-hidden">
                        <div className="h-full rounded-full bg-teal-light transition-all" style={{ width: `${progress * 100}%` }} />
                      </div>
                      <button onClick={togglePause} className="text-[10px] text-grey-mid hover:text-white transition-colors shrink-0">
                        {isPlaying ? "⏸" : "▶"}
                      </button>
                    </>
                  )}
                  {audioState === "idle" && (
                    <span className="font-mono text-[9px] text-grey-dark flex-1">Audio complete</span>
                  )}
                </div>

                {/* Nav buttons */}
                <div className="flex items-center gap-1.5 pt-0.5">
                  <button
                    onClick={handlePrev}
                    disabled={stepIdx === 0}
                    className="rounded-lg border border-white/10 px-2.5 py-1.5 text-[10px] text-grey-mid hover:text-white hover:border-white/25 transition-all disabled:opacity-25 disabled:cursor-not-allowed"
                  >
                    ←
                  </button>
                  <button
                    onClick={handleNext}
                    className="flex-1 rounded-lg bg-teal-light py-1.5 text-[10px] font-bold uppercase tracking-[0.15em] text-navy hover:brightness-110 transition-all"
                  >
                    {isLast ? "Finish ✓" : "Next →"}
                  </button>
                  <button
                    onClick={endTour}
                    className="rounded-lg border border-white/10 px-2.5 py-1.5 text-[10px] text-grey-dark hover:text-grey-mid transition-colors"
                  >
                    Skip
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
