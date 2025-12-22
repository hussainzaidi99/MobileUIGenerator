// frontend/poc-project/src/App.jsx - FINAL PRODUCTION VERSION WITH DARK VEIL
import React, { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import CanvasRendererLite from "./components/CanvasRendererLite";
import CodePreview from "./components/CodePreview";
import ExportButton from "./components/ExportButton";
import ConversationalEditPanel from "./components/ConversationalEditPanel";
import { getPresetById, PRESET_PROMPTS } from "./constants/presetPrompts";
import "./index.css";
import { useAuth } from "./contexts/AuthContext";
import DarkVeil from './components/backgrounds/DarkVeil';


export default function App() {
  const [layout, setLayout] = useState(null);
  const [rnCode, setRnCode] = useState(null);
  const [loading, setLoading] = useState(false);
  const [prompt, setPrompt] = useState("");
  const [error, setError] = useState(null);
  const [showCode, setShowCode] = useState(false);
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
  
  // ✅ NEW: Mobile detection for optimized Dark Veil
  const [isMobile, setIsMobile] = useState(false);

  const { user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const userId = user?.id;

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
    } finally {
      setEnhancing(false);
    }
  };

  const generate = async () => {
    if (!userId) {
      navigate('/auth', { 
        state: { from: location },
        replace: false 
      });
      return;
    }

    const finalPrompt = prompt.trim();

    if (!finalPrompt) {
      setError("Please enter a prompt or select a preset.");
      return;
    }

    setLoading(true);
    setError(null);
    setProcessingStage("Analyzing your request...");

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
          setError(
            `Insufficient credits. You need ${errorData.details?.required_credits?.toFixed(4)} credits but have ${errorData.details?.current_credits?.toFixed(4)} credits.`
          );
          setShowInsufficientCreditsModal(true);
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
              user_id: userId
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

      setProcessingStage("Complete!");
      setTimeout(() => setProcessingStage(""), 2000);
      
      fetchUserCredits();
    } catch (e) {
      console.error("Generation error:", e);
      setError(e.message || "Generation failed. Please try again.");
      setProcessingStage("");
    } finally {
      setLoading(false);
    }
  };

  const handleLayoutUpdate = (newLayout) => {
    console.log("🔄 Layout updated from edit panel:", newLayout);
    
    setLayout({
      ...newLayout,
      _timestamp: Date.now()
    });
    
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
  };

  const screenCount = layout?.screens?.length || 0;
  const isSplitView = layout || loading;

  const displayedPresets = showAllPresets 
    ? PRESET_PROMPTS 
    : PRESET_PROMPTS.slice(0, 3);

  return (
    <div className="app-container stitch-layout">
      {/* ✅ MOBILE-OPTIMIZED DARK VEIL BACKGROUND */}
      {isMobile ? (
        // Mobile: Static, fewer particles for better performance
        <DarkVeil 
          opacity={0.25}
          particleCount={15}
          enableAnimation={false}
          showMesh={false}
        />
      ) : (
        // Desktop: Full animated experience
        <DarkVeil 
          opacity={0.4}
          particleCount={40}
          enableAnimation={true}
          showMesh={true}
        />
      )}

      {/* Insufficient Credits Modal */}
      {showInsufficientCreditsModal && (
        <div className="credits-modal-overlay" onClick={() => setShowInsufficientCreditsModal(false)}>
          <div className="credits-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-icon">💳</div>
            <h2 className="modal-title">Insufficient Credits</h2>
            <p className="modal-message">
              {error || "You don't have enough credits. Please purchase more to continue."}
            </p>
            <div className="modal-actions">
              <button 
                className="modal-btn modal-btn-primary"
                onClick={() => {
                  setShowInsufficientCreditsModal(false);
                  navigate('/pricing');
                }}
              >
                Buy Credits
              </button>
              <button 
                className="modal-btn modal-btn-secondary"
                onClick={() => setShowInsufficientCreditsModal(false)}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Main Split Layout */}
      <div className={`stitch-main-container ${isSplitView ? 'split-mode' : 'center-mode'}`}>
        
        {/* Left Panel */}
        <div className={`stitch-left-panel ${isSplitView ? 'expanded' : ''}`}>
          
          {/* CENTER MODE: Hero + Input */}
          {!isSplitView && (
            <div className="stitch-hero-content">
              <h1 className="stitch-title">
                Generate Your Dream Mobile<br />
                User Interfaces with <span className="gradient-text-stitch">AI</span>
              </h1>

              <p className="stitch-subtitle">
                Simply describe the Mobile UI you envision, and our advanced AI will<br />
                build, design & write content for you instantly. No coding required.
              </p>

              <div className="stitch-input-wrapper-center">
                <div className="stitch-input-container">
                  <div className="sparkle-icon-stitch">✨</div>
                  <textarea
                    className="stitch-input"
                    rows={1}
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    placeholder="Describe your mobile UI (e.g., 'A minimalist portfolio for a photographer')"
                    disabled={loading || enhancing}
                  />
                  
                  <button
                    onClick={generate}
                    className="stitch-btn-inline"
                    disabled={loading || enhancing || !prompt.trim()}
                  >
                    {loading ? (
                      <>
                        <span className="spinner-small"></span>
                        Generating
                      </>
                    ) : (
                      <>
                        Generate UI
                        <span className="arrow-icon-stitch">→</span>
                      </>
                    )}
                  </button>
                </div>

                {/* Credits Estimate */}
                {estimatedCost && !loading && (
                  <div 
                    className="credits-estimate-card"
                    style={{
                      padding: '14px 18px',
                      background: 'rgba(59, 130, 246, 0.1)',
                      border: '2px solid rgba(59, 130, 246, 0.3)',
                      borderRadius: '12px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '12px',
                      animation: 'fadeIn 0.3s ease-out',
                    }}
                  >
                    <span style={{ fontSize: '20px' }}>ℹ️</span>
                    <div style={{ flex: 1 }}>
                      <div style={{ 
                        fontSize: '13px', 
                        fontWeight: '700',
                        color: '#3B82F6',
                        marginBottom: '2px'
                      }}>
                        Estimated Cost
                      </div>
                      <div style={{ 
                        fontSize: '12px', 
                        color: '#60A5FA',
                        fontWeight: '600'
                      }}>
                        ~{estimatedCost.credits.toFixed(4)} credits 
                        ({new Intl.NumberFormat().format(estimatedCost.tokens)} tokens)
                        {userCredits && (
                          <span style={{ marginLeft: '8px', opacity: 0.8 }}>
                            • You have: {userCredits.credits.toFixed(4)} credits
                          </span>
                        )}
                      </div>
                      <div style={{
                        fontSize: '11px',
                        color: '#93C5FD',
                        marginTop: '4px',
                        fontStyle: 'italic'
                      }}>
                        This is an estimate. Actual cost may vary.
                      </div>
                    </div>
                  </div>
                )}

                <div className="stitch-initial-controls">
                  <button
                    onClick={enhancePrompt}
                    className="stitch-text-btn"
                    disabled={enhancing || loading || !prompt.trim()}
                  >
                    {enhancing ? 'Enhancing...' : '✨ Enhance Prompt'}
                  </button>
                  
                  <div className="stitch-presets-row">
                    {displayedPresets.map((preset) => (
                      <button
                        key={preset.id}
                        onClick={() => handlePresetClick(preset.id)}
                        className={`stitch-preset-chip-small ${selectedPreset === preset.id ? 'active' : ''}`}
                      >
                        {preset.label}
                      </button>
                    ))}
                    
                    {PRESET_PROMPTS.length > 3 && (
                      <button
                        onClick={() => setShowAllPresets(!showAllPresets)}
                        className="stitch-preset-chip-small"
                        style={{
                          background: 'rgba(99, 102, 241, 0.1)',
                          border: '1px solid rgba(99, 102, 241, 0.3)',
                          color: '#667EEA',
                          fontWeight: '700'
                        }}
                      >
                        {showAllPresets ? '↑ Show Less' : `↓ ${PRESET_PROMPTS.length - 3} More`}
                      </button>
                    )}
                  </div>
                </div>
              </div>

              {/* Error Message */}
              {error && !loading && (
                <div className="stitch-error" style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  padding: '16px 20px',
                  background: 'rgba(239, 68, 68, 0.1)',
                  border: '2px solid rgba(239, 68, 68, 0.2)',
                  borderRadius: '12px',
                  color: '#DC2626',
                  fontSize: '14px',
                  fontWeight: '600',
                  marginTop: '16px'
                }}>
                  <span style={{ fontSize: '20px' }}>⚠️</span>
                  <span>{error}</span>
                </div>
              )}
            </div>
          )}

          {/* SPLIT MODE: Sidebar with Conversation */}
          {isSplitView && (
            <div className="stitch-sidebar-content">
              <div className="stitch-sidebar-header">
                <span className="logo-text">AppGen</span>
                <button 
                  onClick={handleNewGeneration} 
                  className="new-chat-btn" 
                  title="New Project"
                >
                  +
                </button>
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
                  <p>{processingStage || "Getting things ready..."}</p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right Panel - Preview/Code Canvas */}
        <div className={`stitch-right-panel ${isSplitView ? 'visible' : ''}`}>
          {/* Floating Toolbar */}
          {isSplitView && layout && (
            <div className="stitch-floating-toolbar">
              <div className="toolbar-group">
                <button
                  onClick={toggleCodeView}
                  className={`toolbar-btn ${showCode ? 'active' : ''}`}
                  title={showCode ? "Show Preview" : "Show Code"}
                >
                  {showCode ? '📱 Preview' : '💻 Code'}
                </button>
                
                
                {rnCode && Object.keys(rnCode).length > 0 && (
                  <ExportButton rnCode={rnCode} className="toolbar-btn" />
                )}
              </div>
            </div>
          )}

          {/* Canvas Content */}
          {loading ? (
            <div className="stitch-canvas-placeholder" style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              height: '100%',
              padding: '60px 40px',
              textAlign: 'center',
              color: 'white'
            }}>
              <div className="placeholder-icon" style={{
                fontSize: '120px',
                marginBottom: '32px',
                opacity: 0.9,
                animation: 'float 3s ease-in-out infinite'
              }}>📱</div>
              <div className="placeholder-text" style={{
                fontSize: '28px',
                fontWeight: '800',
                marginBottom: '16px',
                textShadow: '0 2px 16px rgba(0, 0, 0, 0.2)'
              }}>Generating your UI...</div>
              <div className="placeholder-progress" style={{ width: '100%', maxWidth: '400px' }}>
                <div className="progress-bar" style={{
                  width: '100%',
                  height: '8px',
                  background: '#E2E8F0',
                  borderRadius: '10px',
                  overflow: 'hidden'
                }}>
                  <div className="progress-fill" style={{
                    height: '100%',
                    background: 'linear-gradient(90deg, #667EEA, #764BA2)',
                    borderRadius: '10px',
                    animation: 'progressFill 2s ease-in-out infinite'
                  }}></div>
                </div>
              </div>
            </div>
          ) : layout ? (
            <div className="stitch-canvas-container">
              {!showCode ? (
                <div className="phone-mockups-grid">
                  {layout.screens?.map((screen, idx) => (
                    <div key={`${screen.name || idx}-${layout._timestamp || ''}`} className="phone-mockup">
                      <div className="phone-frame-wrapper">
                        <div className="phone-notch"></div>
                        
                        <div className="phone-screen-area">
                          <div className="phone-screen-header">
                            <div className="screen-name-display">
                              {screen.name || `Screen ${idx + 1}`}
                            </div>
                          </div>
                          
                          <div className="phone-screen-content">
                            <CanvasRendererLite 
                              key={`canvas-${screen.name || idx}-${layout._timestamp || ''}`}
                              layout={{ 
                                screens: [screen],
                                theme: layout.theme,
                                tokens: layout.tokens
                              }} 
                            />
                          </div>
                          
                          <div className="phone-home-indicator"></div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                rnCode && Object.keys(rnCode).length > 0 ? (
                  <CodePreview rnCode={rnCode} />
                ) : (
                  <div className="empty-state" style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    height: '100%',
                    padding: '60px 40px',
                    textAlign: 'center',
                    color: 'white'
                  }}>
                    <div className="empty-icon" style={{ fontSize: '120px', marginBottom: '32px' }}>📄</div>
                    <h3 className="empty-title" style={{ fontSize: '28px', fontWeight: '800' }}>No Code Generated</h3>
                  </div>
                )
              )}
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}