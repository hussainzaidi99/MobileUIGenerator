// frontend/poc-project/src/App.jsx - PRODUCTION READY with Edit Panel
import React, { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import CanvasRendererLite from "./components/CanvasRendererLite";
import CodePreview from "./components/CodePreview";
import ExportButton from "./components/ExportButton";
import ConversationalEditPanel from "./components/ConversationalEditPanel";
import { getPresetById, PRESET_PROMPTS } from "./constants/presetPrompts";
import "./index.css";
import { useAuth } from "./contexts/AuthContext";

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

  // ✅ Edit Session State
  const [sessionId, setSessionId] = useState(null);
  const [showEditPanel, setShowEditPanel] = useState(false);

  const { user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const userId = user?.id;

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

  // Token estimation
  useEffect(() => {
    if (prompt.trim().length > 20) {
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
  }, [prompt]);

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

      // ✅ CREATE EDIT SESSION
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
          setShowEditPanel(true);
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

  // ✅ Layout update handler for edit panel
  const handleLayoutUpdate = (newLayout) => {
    console.log("📝 Layout updated from edit panel");
    setLayout(newLayout);
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
    setShowEditPanel(false);
  };

  const screenCount = layout?.screens?.length || 0;

  return (
    <div className="app-container stitch-layout">
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
      <div className={`stitch-main-container ${layout || loading ? 'split-mode' : 'center-mode'}`}>
        
        {/* Left Panel - Input & Controls */}
        <div className={`stitch-left-panel ${layout || loading ? 'collapsed' : ''}`}>
          <div className="stitch-input-section">
            
            {/* Hero Content */}
            {!layout && !loading && (
              <>
                <h1 className="stitch-title">
                  Generate Your Dream Mobile<br />
                  User Interfaces with <span className="gradient-text-stitch">AI</span>
                </h1>

                <p className="stitch-subtitle">
                  Simply describe the Mobile UI you envision, and our advanced AI will<br />
                  build, design & write content for you instantly. No coding required.
                </p>
              </>
            )}

            {/* Input Area */}
            <div className="stitch-input-wrapper">
              <div className="stitch-input-container">
                <div className="sparkle-icon-stitch">✨</div>
                <textarea
                  className="stitch-input"
                  rows={1}
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  placeholder="Describe your mobile UI (e.g., 'A minimalist portfolio for a photographer')"
                  disabled={loading || enhancing}
                  style={{
                    paddingRight: (layout || loading) ? '14px' : '160px'
                  }}
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
              {estimatedCost && !loading && !layout && (
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

              {/* Enhance Button */}
              {!layout && !loading && (
                <button
                  onClick={enhancePrompt}
                  className="stitch-enhance-btn"
                  disabled={enhancing || loading || !prompt.trim()}
                >
                  {enhancing ? (
                    <>
                      <span className="spinner-small"></span>
                      Enhancing...
                    </>
                  ) : (
                    <>
                      <span className="btn-icon">✨</span>
                      Enhance Prompt
                    </>
                  )}
                </button>
              )}
            </div>

            {/* Preset Chips */}
            {!layout && !loading && (
              <div className="stitch-presets">
                {PRESET_PROMPTS.map((preset) => (
                  <button
                    key={preset.id}
                    onClick={() => handlePresetClick(preset.id)}
                    className={`stitch-preset-chip ${selectedPreset === preset.id ? 'active' : ''}`}
                  >
                    <span className="preset-icon-stitch">{preset.icon}</span>
                    <span className="preset-label-stitch">{preset.label}</span>
                  </button>
                ))}
              </div>
            )}

            {/* Processing Stage */}
            {loading && processingStage && (
              <div className="stitch-processing">
                <div className="processing-spinner"></div>
                <div className="processing-content">
                  <div className="processing-title">{processingStage}</div>
                  <div className="processing-subtitle">Estimated time: 100 seconds</div>
                </div>
              </div>
            )}

            {/* Error Message */}
            {error && !loading && (
              <div className="stitch-error">
                <span className="error-icon">⚠️</span>
                <span>{error}</span>
              </div>
            )}

            {/* ✅ CONVERSATIONAL EDIT PANEL */}
            {layout && !loading && sessionId && showEditPanel && (
              <ConversationalEditPanel
                sessionId={sessionId}
                userId={userId}
                onLayoutUpdate={handleLayoutUpdate}
                apiBaseUrl={import.meta.env.VITE_API_BASE_URL}
              />
            )}

            {/* Toolbar (when results are ready) */}
            {layout && !loading && (
              <div className="stitch-results-actions">
                
                {/* ✅ EDIT TOGGLE BUTTON */}
                {sessionId && (
                  <button 
                    onClick={() => setShowEditPanel(!showEditPanel)}
                    className={`stitch-btn ${showEditPanel ? 'stitch-btn-primary' : 'stitch-btn-secondary'}`}
                    title={showEditPanel ? "Hide Edit Panel" : "Show Edit Panel"}
                  >
                    <span style={{ fontSize: '16px' }}>
                      {showEditPanel ? '💬' : '✏️'}
                    </span>
                    {showEditPanel ? 'Editing' : 'Edit'}
                  </button>
                )}

                <button 
                  onClick={toggleCodeView} 
                  className="stitch-btn stitch-btn-secondary"
                  title={showCode ? "View Preview" : "View Code"}
                >
                  {showCode ? (
                    <>
                      <span style={{ fontSize: '16px' }}>👁️</span>
                      Preview
                    </>
                  ) : (
                    <>
                      <span style={{ fontSize: '16px' }}>💻</span>
                      Code
                    </>
                  )}
                </button>

                {rnCode && Object.keys(rnCode).length > 0 && (
                  <ExportButton rnCode={rnCode} />
                )}

                <button 
                  onClick={handleNewGeneration} 
                  className="stitch-btn stitch-btn-secondary"
                  title="Start New Generation"
                >
                  <span style={{ fontSize: '16px' }}>🔄</span>
                  New
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Right Panel - Preview/Code Canvas */}
        <div className={`stitch-right-panel ${layout || loading ? 'visible' : ''}`}>
          {loading ? (
            <div className="stitch-canvas-placeholder">
              <div className="placeholder-icon">📱</div>
              <div className="placeholder-text">Generating your UI...</div>
              <div className="placeholder-progress">
                <div className="progress-bar">
                  <div className="progress-fill"></div>
                </div>
              </div>
            </div>
          ) : layout ? (
            <div className="stitch-canvas-container">
              {!showCode ? (
                <>
                  <div className="canvas-header">
                    <h3 className="canvas-title">Preview</h3>
                    <span className="canvas-badge">
                      {screenCount} screen{screenCount > 1 ? "s" : ""}
                    </span>
                  </div>
                  
                  {/* Phone Mockups Grid */}
                  <div className="phone-mockups-grid">
                    {layout.screens?.map((screen, idx) => (
                      <div key={screen.name || idx} className="phone-mockup">
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
                </>
              ) : (
                rnCode && Object.keys(rnCode).length > 0 ? (
                  <CodePreview rnCode={rnCode} />
                ) : (
                  <div className="empty-state">
                    <div className="empty-icon">📄</div>
                    <h3 className="empty-title">No Code Generated</h3>
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