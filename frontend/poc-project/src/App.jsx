// frontend/poc-project/src/App.jsx - ENHANCED WITH TOAST NOTIFICATIONS
import React, { useState, useEffect, useRef } from "react";
import { useNavigate, useLocation } from "react-router-dom";

import CanvasRendererLite from "./components/CanvasRendererLite";
import CodePreview from "./components/CodePreview";
import { toast } from './utils/toast';
import { WavyBars } from 'spinny-loader';

import ExportButton from "./components/ExportButton";
import Sidebar from "./components/Sidebar";
import ConversationalEditPanel from "./components/ConversationalEditPanel";
import { getPresetById, PRESET_PROMPTS } from "./constants/presetPrompts";
import "./index.css";
import { useAuth } from "./contexts/AuthContext";
import DarkVeil from './components/backgrounds/DarkVeil';
import useAutoResize from "./hooks/useAutoResize";


export default function App({ onSplitModeChange }) {
  const [layout, setLayout] = useState(null);
  const [rnCode, setRnCode] = useState(null);
  const [loading, setLoading] = useState(false);
  const [prompt, setPrompt] = useState("");
  const [error, setError] = useState(null);
  const [showCode, setShowCode] = useState(false);
  const [showSidebar, setShowSidebar] = useState(window.innerWidth > 1400); // Default open on large screens
  const [processingStage, setProcessingStage] = useState("");
  const [enhancing, setEnhancing] = useState(false);
  const [selectedPreset, setSelectedPreset] = useState(null);
  const [showInsufficientCreditsModal, setShowInsufficientCreditsModal] = useState(false);
  const [estimatedCost, setEstimatedCost] = useState(null);
  const [userCredits, setUserCredits] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [showAllPresets, setShowAllPresets] = useState(false);
  // 1. Add state at the top of App component
  const [fullScreenMode, setFullScreenMode] = useState(false);
  const [modalType, setModalType] = useState('insufficient'); // 'insufficient' or 'low'

  // ✅ NEW: Mobile detection for optimized Dark Veil
  const [isMobile, setIsMobile] = useState(false);

  const { user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const userId = user?.id;

  // ✅ Auto-expanding textarea ref
  const textareaRef = useRef(null);

  // ✅ Auto-resizing textarea hook
  useAutoResize(textareaRef, prompt);

  // ✅ NEW: Detect mobile devices
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth <= 768);
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);

    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  useEffect(() => {
    if (userId) {
      fetchUserCredits();
    }
  }, [userId]);

  // ✅ NEW: Restore state on initial mount
  const [hasRestored, setHasRestored] = useState(false);

  // ✅ NEW: Persist state to localStorage whenever it changes
  useEffect(() => {
    // Only persist for logged-in users AND after we've attempted restoration
    if (userId && hasRestored) {
      const stateToSave = {
        layout,
        rnCode,
        prompt,
        sessionId,
        loading,
        processingStage, // NEW: Persist the stage (Analyzing, Structuring, etc.)
        userId
      };

      localStorage.setItem(`stitch_state_${userId}`, JSON.stringify(stateToSave));
      // console.log("💾 State persisted to localStorage");
    }
  }, [layout, rnCode, prompt, sessionId, loading, processingStage, userId, hasRestored]);

  useEffect(() => {
    if (userId && !hasRestored) {
      const saved = localStorage.getItem(`stitch_state_${userId}`);
      if (saved) {
        try {
          const {
            layout: savedLayout,
            rnCode: savedRnCode,
            prompt: savedPrompt,
            sessionId: savedSessionId,
            loading: wasLoading,
            processingStage: savedStage, // Restore stage
            userId: savedUserId
          } = JSON.parse(saved);

          if (savedUserId === userId) {
            if (savedLayout) setLayout(savedLayout);
            if (savedRnCode) setRnCode(savedRnCode);
            if (savedPrompt) setPrompt(savedPrompt);
            if (savedSessionId) setSessionId(savedSessionId);
            if (savedStage) setProcessingStage(savedStage);

            // Auto-resume if it was generating
            if (wasLoading && savedPrompt && !savedLayout) {
              console.log("🔄 Resuming interrupted generation for prompt:", savedPrompt);
              // Pass prompt directly to ensure it doesn't use empty state due to batched update
              setTimeout(() => {
                generate(savedPrompt);
              }, 500);
            }
          }
        } catch (e) {
          console.error("Failed to restore state:", e);
        }
      }
      setHasRestored(true);
    }
  }, [userId, hasRestored]);

  const fetchUserCredits = async () => {
    if (!userId) return;

    try {
      const res = await fetch(
        `${import.meta.env.VITE_API_BASE_URL}/payment/balance/${userId}`
      );

      if (res.ok) {
        const data = await res.json();
        setUserCredits(data);
      }
    } catch (error) {
      console.error("Failed to fetch credits:", error);
    }
  };

  // Token estimation (only show in center mode)
  useEffect(() => {
    if (prompt.trim().length > 20 && !layout) {
      const wordCount = prompt.trim().split(/\s+/).length;
      const sentenceCount = prompt.split(/[.!?]+/).filter(s => s.trim()).length;
      const hasMultipleScreens = /screen|page|tab/i.test(prompt);
      const hasComplexFeatures = /animation|interaction|chart|graph|map/i.test(prompt);

      let estimatedTokens = 15000;

      if (wordCount > 100 || sentenceCount > 5 || hasComplexFeatures) {
        estimatedTokens = 25000;
      } else if (wordCount > 50 || sentenceCount > 3 || hasMultipleScreens) {
        estimatedTokens = 20000;
      }

      estimatedTokens += Math.floor(wordCount / 50) * 1000;
      estimatedTokens = Math.min(estimatedTokens, 35000);

      const estimatedCredits = estimatedTokens / 70000;

      setEstimatedCost({
        tokens: estimatedTokens,
        credits: estimatedCredits
      });
    } else {
      setEstimatedCost(null);
    }
  }, [prompt, layout]);

  // ✅ Handle textarea change
  const handleTextareaChange = (e) => {
    setPrompt(e.target.value);
  };

  const enhancePrompt = async () => {
    if (!userId) {
      navigate('/auth', {
        state: { from: location },
        replace: false
      });
      return;
    }
    if (!prompt.trim()) return;

    setEnhancing(true);
    setError(null);

    try {
      const res = await fetch(`${import.meta.env.VITE_API_BASE_URL}/refine`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: prompt.trim() }),
      });

      if (!res.ok) {
        const text = await res.text();
        throw new Error(`Enhancement failed: ${res.status} ${text}`);
      }

      const data = await res.json();

      if (data.refinement_applied && data.refined_prompt) {
        setPrompt(data.refined_prompt);
      } else {
        setError("Prompt is already detailed enough – no changes made.");
      }
    } catch (e) {
      console.error("Prompt enhancement error:", e);
      setError(e.message || "Failed to enhance prompt. Please try again.");
      toast.error("Enhancement Failed", e.message || "Failed to enhance prompt.");
    } finally {
      setEnhancing(false);
    }
  };

  const generate = async (overridePrompt = null) => {
    if (!userId) {
      toast.info("Authentication Required", "Please sign in or sign up to start building your screens.");
      navigate('/auth', {
        state: { from: location },
        replace: false
      });
      return;
    }

    // Use overridePrompt if provided (for auto-resume), otherwise use current state
    // Ensure we don't try to .trim() an event object from a button click
    const promptToUse = (typeof overridePrompt === 'string') ? overridePrompt : prompt;
    const finalPrompt = (promptToUse || "").trim();

    if (!finalPrompt) {
      setError("Please enter a prompt or select a preset.");
      toast.info("Input Required", "Please enter a prompt or select a preset.");
      return;
    }

    setLoading(true);
    setError(null);
    setProcessingStage("Analyzing your request...");

    // NEW: Show starting toast (info or loading)
    const generationToastId = toast.loading("Processing your request...");

    try {
      const res = await fetch(
        `${import.meta.env.VITE_API_BASE_URL}/generate_pipeline`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            prompt: finalPrompt,
            user_id: userId
          }),
        }
      );

      if (!res.ok) {
        const errorData = await res.json();

        if (res.status === 402) {
          const required = errorData.details?.required_credits?.toFixed(4) || "0.0000";
          const current = errorData.details?.current_credits?.toFixed(4) || userCredits?.credits?.toFixed(4) || "0.0000";

          setError(
            `Insufficient credits. You need ${required} credits but have ${current} credits.`
          );
          setModalType('insufficient');
          setShowInsufficientCreditsModal(true);
          setLoading(false); // Stop loading on credit error
          return;
        }

        throw new Error(errorData.error || `Server error: ${res.status}`);
      }

      setProcessingStage("Structuring components...");
      await new Promise(resolve => setTimeout(resolve, 800));

      const data = await res.json();

      setProcessingStage("Generating UI preview...");
      await new Promise(resolve => setTimeout(resolve, 600));

      setLayout(data?.web_preview || data?.component_model);
      setRnCode(data?.react_native_code || {});

      // Create edit session
      try {
        const sessionRes = await fetch(
          `${import.meta.env.VITE_API_BASE_URL}/create-edit-session`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              component_model: data?.component_model,
              web_preview: data?.web_preview,
              react_native_code: data?.react_native_code,
              user_id: userId,
              title: data?.project_title || "New Project"
            })
          }
        );

        if (sessionRes.ok) {
          const sessionData = await sessionRes.json();
          setSessionId(sessionData.session_id);
          console.log("✅ Edit session created:", sessionData.session_id);
        } else {
          console.error("Failed to create edit session:", await sessionRes.text());
        }
      } catch (err) {
        console.error("Failed to create edit session:", err);
      }

      if (data?.react_native_code && Object.keys(data.react_native_code).length > 0) {
        setShowCode(false);
      }

      // ✅ SUCCESS: Update local credits
      await fetchUserCredits();

      // NEW: Show success toast
      toast.success("Generation Complete!", "Your UI has been successfully built.");
      toast.dismiss(generationToastId);

      // ✅ NEW: Show low credits warning if < 10 (and not already showing insufficient)
      if (userCredits && userCredits.credits < 10) {
        console.log("⚠️ Low credits warning (< 10 credits remaining)");
        setModalType('low');
        setShowInsufficientCreditsModal(true);
      }
    } catch (e) {
      console.error("Generation error:", e);
      setError(e.message || "Generation failed. Please try again.");
      toast.error("Generation failed", e.message || "Please try again later.");
      setProcessingStage("");
      if (typeof generationToastId !== 'undefined') toast.dismiss(generationToastId);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectConversation = async (convId) => {
    setLoading(true);
    setError(null);
    setProcessingStage("Loading project...");

    try {
      const res = await fetch(`${import.meta.env.VITE_API_BASE_URL}/edit-session/${convId}`);
      if (!res.ok) throw new Error("Failed to load conversation");

      const data = await res.json();

      // Load state
      setSessionId(data.session_id);
      setLayout(data?.web_preview || data?.component_model);
      setRnCode(data?.react_native_code || {});
      setShowCode(false);
      setPrompt(""); // Clear search prompt

      console.log("✅ Project loaded:", convId);
    } catch (err) {
      console.error("Load error:", err);
      setError("Failed to load project history.");
      toast.error("Load Failed", "Failed to load project history.");
    } finally {
      setLoading(false);
      setProcessingStage("");
    }
  };

  const handleLayoutUpdate = (newLayout, newRnCode) => {
    console.log("🔄 Layout updated from edit panel:", newLayout);

    setLayout({
      ...newLayout,
      _timestamp: Date.now()
    });

    if (newRnCode) {
      console.log("🔄 Code updated from edit panel");
      setRnCode(newRnCode);
    }

    console.log("✅ Layout state updated, component should re-render");
  };

  const toggleCodeView = () => setShowCode((prev) => !prev);

  const handlePresetClick = (presetId) => {
    setSelectedPreset(presetId);
    const preset = getPresetById(presetId);
    if (preset) {
      setPrompt(preset.prompt);
    }
  };

  const handleNewGeneration = () => {
    setLayout(null);
    setRnCode(null);
    setShowCode(false);
    setPrompt("");
    setSelectedPreset(null);
    setError(null);
    setProcessingStage("");
    setEstimatedCost(null);
    setSessionId(null);
    if (userId) {
      localStorage.removeItem(`stitch_state_${userId}`);
    }
  };

  const toggleSidebar = () => setShowSidebar(prev => !prev);

  const screenCount = layout?.screens?.length || 0;
  const isSplitView = !!(layout || loading); // Ensure boolean

  // ✅ NEW: Sync split mode state with parent to show/hide navbar
  useEffect(() => {
    onSplitModeChange?.(isSplitView);
  }, [isSplitView, onSplitModeChange]);

  const displayedPresets = showAllPresets
    ? PRESET_PROMPTS
    : PRESET_PROMPTS.slice(0, 3);

  return (
    <div className="app-container stitch-layout">

      {/* Dark Veil background */}
      {isMobile ? (
        <DarkVeil opacity={0.25} particleCount={15} enableAnimation={false} showMesh={false} />
      ) : (
        <DarkVeil opacity={0.4} particleCount={40} enableAnimation={true} showMesh={true} />
      )}

      {/* Credits Modals */}
      {showInsufficientCreditsModal && (
        <div className="credits-modal-overlay" onClick={() => setShowInsufficientCreditsModal(false)}>
          <div className="credits-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-icon">{modalType === 'insufficient' ? '💳' : '⚠️'}</div>
            <h2 className="modal-title">{modalType === 'insufficient' ? 'Insufficient Credits' : 'Low Credits Warning'}</h2>
            <p className="modal-message">
              {modalType === 'insufficient' ? (error || "You don't have enough credits.") : `Low credits (${userCredits?.credits?.toFixed(2)} left).`}
            </p>
            <div className="modal-actions">
              <button className="modal-btn modal-btn-primary" onClick={() => navigate('/pricing')}>Buy Credits</button>
              <button className="modal-btn modal-btn-secondary" onClick={() => setShowInsufficientCreditsModal(false)}>Close</button>
            </div>
          </div>
        </div>
      )}

      <div className={`stitch-main-layout ${!showSidebar ? 'sidebar-collapsed' : ''}`}>
        {/* Sidebar Toggle Trigger (Floating or Header) */}
        {!showSidebar && !isSplitView && (
          <button onClick={toggleSidebar} className="stitch-sidebar-toggle-btn floating">
            📁
          </button>
        )}

        {/* HISTORY SIDEBAR */}
        {userId && (
          <Sidebar
            userId={userId}
            activeSessionId={sessionId}
            onSelectConversation={handleSelectConversation}
            onNewProject={handleNewGeneration}
            apiBaseUrl={import.meta.env.VITE_API_BASE_URL}
            onClose={() => setShowSidebar(false)} // Optional: close on mobile/select
          />
        )}

        <div className="stitch-content-area">
          <div className={`stitch-main-container ${isSplitView ? 'split-mode' : 'center-mode'}`}>
            <div className={`stitch-left-panel ${isSplitView ? 'expanded' : ''}`}>
              {!isSplitView && (
                <div className="stitch-hero-content">
                  <h1 className="stitch-title">Generate Your Dream Mobile UI with <span className="gradient-text-stitch">AI</span></h1>
                  <p className="stitch-subtitle">Describe your vision, and we'll build it instantly.</p>

                  <div className="stitch-input-wrapper-center">
                    <div className="stitch-input-container">
                      <textarea
                        ref={textareaRef}
                        className="stitch-input"
                        rows={1}
                        value={prompt}
                        onChange={handleTextareaChange}
                        placeholder="Describe your mobile UI..."
                        disabled={loading || enhancing}
                        style={{
                          minHeight: '60px',
                          maxHeight: '300px',
                          overflow: 'auto',
                          resize: 'none'
                        }}
                      />
                      <button onClick={generate} className="stitch-btn-inline" disabled={loading || enhancing || !prompt.trim()}>
                        {loading ? 'Generating...' : 'Generate UI →'}
                      </button>
                    </div>

                    <div className="stitch-initial-controls">
                      <button onClick={enhancePrompt} className="stitch-text-btn" disabled={enhancing || loading || !prompt.trim()}>
                        {enhancing ? 'Enhancing...' : '✨ Enhance Prompt'}
                      </button>
                      <div className="stitch-presets-row">
                        {displayedPresets.map(preset => (
                          <button key={preset.id} onClick={() => handlePresetClick(preset.id)} className="stitch-preset-chip-small">
                            {preset.label}
                          </button>
                        ))}
                        <button
                          onClick={() => setShowAllPresets(!showAllPresets)}
                          className="stitch-see-more-btn"
                        >
                          {showAllPresets ? 'Less' : 'More'}
                        </button>
                      </div>
                    </div>
                  </div>

                </div>
              )}

              {isSplitView && (
                <div className="stitch-sidebar-content">
                  <div className="stitch-sidebar-header">
                    <button onClick={toggleSidebar} className="sidebar-hide-btn" title="Hide History">
                      {showSidebar ? '◀' : '▶'}
                    </button>
                    <span className="logo-text">AppGen</span>
                    <button onClick={handleNewGeneration} className="new-chat-btn">+</button>
                  </div>
                  {(layout && sessionId) || loading ? (
                    <ConversationalEditPanel
                      sessionId={sessionId}
                      userId={userId}
                      initialPrompt={prompt}
                      onLayoutUpdate={handleLayoutUpdate}
                      apiBaseUrl={import.meta.env.VITE_API_BASE_URL}
                      loading={loading}
                      processingStage={processingStage}
                    />
                  ) : (
                    <div className="stitch-loading-state">
                      <div className="loading-pulse-ring"></div>
                      <p>{processingStage || "Loading..."}</p>
                    </div>
                  )}
                </div>
              )}
            </div>

            <div className={`stitch-right-panel ${isSplitView ? 'visible' : ''}`}>
              {isSplitView && layout && (
                <div className="stitch-floating-toolbar">
                  <div className="toolbar-group">
                    <button onClick={toggleCodeView} className="toolbar-btn">{showCode ? '📱 Preview' : '💻 Code'}</button>
                    {rnCode && <ExportButton rnCode={rnCode} className="toolbar-btn" />}
                  </div>
                </div>
              )}

              {loading ? (
                <div className="stitch-canvas-placeholder">
                  <div className="placeholder-icon">
                    <WavyBars color="#a855f7" />
                  </div>
                  <div className="placeholder-text">{processingStage || "Generating..."}</div>
                </div>
              ) : layout ? (
                <div className="stitch-canvas-container">
                  {!showCode ? (
                    layout.screens && layout.screens.length > 0 ? (
                      <div className="phone-mockups-grid">
                        {layout.screens.map((screen, idx) => (
                          <div key={idx} className="phone-mockup">
                            <div className="phone-frame-wrapper">
                              <div className="phone-notch"></div>
                              <div className="phone-screen-area">
                                <div className="phone-screen-content">
                                  <CanvasRendererLite layout={{ screens: [screen], theme: layout.theme, tokens: layout.tokens }} />
                                </div>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="code-preview-empty">
                        <p>No screens found in design</p>
                      </div>
                    )
                  ) : (
                    <CodePreview rnCode={rnCode} />
                  )}
                </div>
              ) : (
                <div className="stitch-canvas-placeholder">
                  <div className="placeholder-icon">🌑</div>
                  <div className="placeholder-text">Waiting for design data...</div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}