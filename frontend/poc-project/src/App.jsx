// frontend/poc-project/src/App.jsx - COMPLETE FILE WITH CREDITS ESTIMATE
import React, { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import CanvasRendererLite from "./components/CanvasRendererLite";
import CodePreview from "./components/CodePreview";
import ExportButton from "./components/ExportButton";
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
  const [usageStats, setUsageStats] = useState(null);
  const [showInsufficientCreditsModal, setShowInsufficientCreditsModal] = useState(false);

  // ✅ NEW: Credits estimate state
  const [estimatedCost, setEstimatedCost] = useState(null);
  const [userCredits, setUserCredits] = useState(null);
  const [showCostWarning, setShowCostWarning] = useState(false);

  const { user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const userId = user?.id;

  // ✅ NEW: Fetch user credits on mount and when userId changes
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

  // ✅ NEW: Calculate estimated cost whenever prompt changes
  useEffect(() => {
    if (prompt.trim().length > 20) {
      // Estimation logic:
      // - Average: ~5 tokens per word
      // - UI generation uses ~15,000-50,000 tokens depending on complexity
      // - 1 credit = 70,000 tokens
      
      const wordCount = prompt.trim().split(/\s+/).length;
      const sentenceCount = prompt.split(/[.!?]+/).filter(s => s.trim()).length;
      const hasMultipleScreens = /screen|page|tab/i.test(prompt);
      const hasComplexFeatures = /animation|interaction|chart|graph|map/i.test(prompt);
      
      // Base estimate: 20k tokens for simple, 40k for complex
      let estimatedTokens = 20000;
      
      // Adjust based on complexity indicators
      if (wordCount > 100 || sentenceCount > 5 || hasComplexFeatures) {
        estimatedTokens = 45000; // Complex UI
      } else if (wordCount > 50 || sentenceCount > 3 || hasMultipleScreens) {
        estimatedTokens = 32000; // Medium complexity
      }
      
      // Add 3k tokens per 40 words beyond baseline
      estimatedTokens += Math.floor(wordCount / 40) * 3000;
      
      // Cap at reasonable maximum
      estimatedTokens = Math.min(estimatedTokens, 65000);
      
      const estimatedCredits = estimatedTokens / 70000;
      
      setEstimatedCost({
        tokens: estimatedTokens,
        credits: estimatedCredits
      });

      // ✅ Show warning if user doesn't have enough credits
      if (userCredits && estimatedCredits > userCredits.credits) {
        setShowCostWarning(true);
      } else {
        setShowCostWarning(false);
      }
    } else {
      setEstimatedCost(null);
      setShowCostWarning(false);
    }
  }, [prompt, userCredits]);

  const enhancePrompt = async () => {
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
        setError("Prompt is already detailed enough — no changes made.");
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

    // ✅ NEW: Pre-check credits before starting generation
    if (userCredits && estimatedCost && estimatedCost.credits > userCredits.credits) {
      setShowInsufficientCreditsModal(true);
      return;
    }

    setLoading(true);
    setError(null);
    setUsageStats(null);
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

      if (data.usage) {
        setUsageStats(data.usage);
        // ✅ Refresh credits after successful generation
        fetchUserCredits();
      }

      if (data?.react_native_code && Object.keys(data.react_native_code).length > 0) {
        setShowCode(false);
      }

      setProcessingStage("Complete!");
      setTimeout(() => setProcessingStage(""), 2000);
    } catch (e) {
      console.error("Generation error:", e);
      setError(e.message || "Generation failed. Please try again.");
      setProcessingStage("");
    } finally {
      setLoading(false);
    }
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
    setUsageStats(null);
    setError(null);
    setProcessingStage("");
    setEstimatedCost(null);
    setShowCostWarning(false);
  };

  const screenCount = layout?.screens?.length || 0;
  const fileCount = rnCode ? Object.keys(rnCode).length : 0;

  return (
    <div className="app-container stitch-layout">
      {/* Insufficient Credits Modal */}
      {showInsufficientCreditsModal && (
        <div className="credits-modal-overlay" onClick={() => setShowInsufficientCreditsModal(false)}>
          <div className="credits-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-icon">💳</div>
            <h2 className="modal-title">Insufficient Credits</h2>
            <p className="modal-message">
              {estimatedCost ? (
                <>
                  This generation will cost approximately <strong>{estimatedCost.credits.toFixed(4)} credits</strong> (~{new Intl.NumberFormat().format(estimatedCost.tokens)} tokens),
                  but you only have <strong>{userCredits?.credits?.toFixed(4) || 0} credits</strong> available.
                </>
              ) : (
                "You don't have enough credits. Please purchase more to continue."
              )}
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
                    paddingRight: '160px'
                  }}
                  onInput={(e) => {
                    e.target.style.height = 'auto';
                    const newHeight = Math.min(e.target.scrollHeight, 200);
                    e.target.style.height = newHeight + 'px';
                  }}
                />
                
                {/* Generate Button */}
                <button
                  onClick={generate}
                  className="stitch-btn-inline"
                  disabled={loading || enhancing || !prompt.trim() || showCostWarning}
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

              {/* ✅ NEW: Credits Estimate Display */}
              {estimatedCost && !loading && !layout && (
                <div 
                  className="credits-estimate-card"
                  style={{
                    padding: '14px 18px',
                    background: showCostWarning 
                      ? 'rgba(239, 68, 68, 0.1)' 
                      : 'rgba(16, 185, 129, 0.1)',
                    border: showCostWarning 
                      ? '2px solid rgba(239, 68, 68, 0.3)' 
                      : '2px solid rgba(16, 185, 129, 0.3)',
                    borderRadius: '12px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                    animation: 'fadeIn 0.3s ease-out',
                  }}
                >
                  <span style={{ fontSize: '20px' }}>
                    {showCostWarning ? '⚠️' : '💰'}
                  </span>
                  <div style={{ flex: 1 }}>
                    <div style={{ 
                      fontSize: '13px', 
                      fontWeight: '700',
                      color: showCostWarning ? '#DC2626' : '#059669',
                      marginBottom: '2px'
                    }}>
                      {showCostWarning ? 'Insufficient Credits' : 'Estimated Cost'}
                    </div>
                    <div style={{ 
                      fontSize: '12px', 
                      color: showCostWarning ? '#EF4444' : '#10B981',
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
                  </div>
                  {showCostWarning && (
                    <button
                      onClick={() => navigate('/pricing')}
                      style={{
                        padding: '6px 14px',
                        background: 'linear-gradient(135deg, #EF4444, #DC2626)',
                        color: 'white',
                        border: 'none',
                        borderRadius: '8px',
                        fontSize: '12px',
                        fontWeight: '700',
                        cursor: 'pointer',
                        transition: 'all 0.2s',
                        whiteSpace: 'nowrap'
                      }}
                    >
                      Buy Credits
                    </button>
                  )}
                </div>
              )}

              {/* Enhance Button */}
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

            {/* Results Actions */}
            {layout && !loading && (
              <div className="stitch-results-actions">
                <button onClick={toggleCodeView} className="stitch-btn stitch-btn-secondary">
                  {showCode ? "👁️ Preview" : "💻 Code"}
                </button>

                {rnCode && Object.keys(rnCode).length > 0 && (
                  <ExportButton rnCode={rnCode} />
                )}

                <button onClick={handleNewGeneration} className="stitch-btn stitch-btn-secondary">
                  🔄 New
                </button>
              </div>
            )}

            {/* Usage Stats */}
            {usageStats && !loading && (
              <div className="stitch-usage-stats">
                <div className="stat-row">
                  <span className="stat-label">Tokens Used:</span>
                  <span className="stat-value">{new Intl.NumberFormat().format(usageStats.tokens.total_tokens)}</span>
                </div>
                <div className="stat-row">
                  <span className="stat-label">Credits Deducted:</span>
                  <span className="stat-value">{usageStats.credits.credits_deducted?.toFixed(4) || "N/A"}</span>
                </div>
                <div className="stat-row">
                  <span className="stat-label">Remaining Credits:</span>
                  <span className="stat-value">{usageStats.credits.remaining_credits?.toFixed(4) || "N/A"}</span>
                </div>
                <div className="stat-row">
                  <span className="stat-label">Estimated Cost:</span>
                  <span className="stat-value">${usageStats.tokens.estimated_cost?.toFixed(6) || "N/A"}</span>
                </div>
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
                  <CanvasRendererLite layout={layout} />
                </>
              ) : (
                <>
                  <div className="canvas-header">
                    <h3 className="canvas-title">React Native Code</h3>
                    <span className="canvas-badge">
                      {fileCount} file{fileCount > 1 ? "s" : ""}
                    </span>
                  </div>
                  {rnCode && Object.keys(rnCode).length > 0 ? (
                    <CodePreview rnCode={rnCode} />
                  ) : (
                    <div className="empty-state">
                      <div className="empty-icon">📄</div>
                      <h3 className="empty-title">No Code Generated</h3>
                    </div>
                  )}
                </>
              )}
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}