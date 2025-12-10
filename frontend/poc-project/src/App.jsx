// frontend/src/App.jsx - WITH CREDITS INTEGRATION
import React, { useState, useEffect } from "react";
import CanvasRendererLite from "./components/CanvasRendererLite";
import CodePreview from "./components/CodePreview";
import ExportButton from "./components/ExportButton";
import PresetSelector from "./components/PresetSelector";
import { getPresetById } from "./constants/presetPrompts";
import "./index.css";

export default function App() {
  const [layout, setLayout] = useState(null);
  const [rnCode, setRnCode] = useState(null);
  const [loading, setLoading] = useState(false);
  const [prompt, setPrompt] = useState(
    "Modern login and signup screens with social auth"
  );
  const [error, setError] = useState(null);
  const [showCode, setShowCode] = useState(false);
  const [processingStage, setProcessingStage] = useState("");
  const [enhancedPrompt, setEnhancedPrompt] = useState("");
  const [enhancing, setEnhancing] = useState(false);

  // Preset state
  const [inputMode, setInputMode] = useState("manual");
  const [selectedPreset, setSelectedPreset] = useState(null);

  // 🆕 Credits state
  const [userCredits, setUserCredits] = useState(null);
  const [estimatedCost, setEstimatedCost] = useState(null);
  const [usageStats, setUsageStats] = useState(null);
  const [showLowCreditsWarning, setShowLowCreditsWarning] = useState(false);

  // Get user ID from auth (replace with your auth system)
  const userId = localStorage.getItem("user_id") || "demo_user";

  // Fetch user credits on mount
  useEffect(() => {
    fetchUserCredits();
  }, []);

  const fetchUserCredits = async () => {
    try {
      const res = await fetch(
        `${import.meta.env.VITE_API_BASE_URL}/payment/balance/${userId}`
      );
      
      if (res.ok) {
        const data = await res.json();
        setUserCredits(data);
        
        // Show warning if credits are low (less than 10)
        if (data.credits < 10) {
          setShowLowCreditsWarning(true);
        }
      }
    } catch (error) {
      console.error("Failed to fetch credits:", error);
    }
  };

  // Estimate cost before generation
  const estimateCost = (promptText) => {
    const charCount = promptText.length;
    const estimatedTokens = Math.ceil(charCount / 4) * 4; // Rough estimate
    const estimatedCredits = estimatedTokens / 70000;
    
    setEstimatedCost({
      tokens: estimatedTokens,
      credits: estimatedCredits.toFixed(4)
    });
  };

  useEffect(() => {
    if (prompt) {
      estimateCost(prompt);
    }
  }, [prompt]);

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
        setEnhancedPrompt(data.refined_prompt);
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
    // Get final prompt
    let finalPrompt = prompt.trim();

    if (inputMode === "preset" && selectedPreset) {
      const preset = getPresetById(selectedPreset);
      if (preset) {
        finalPrompt = preset.prompt;
      }
    }

    if (!finalPrompt) {
      setError("Please enter a prompt or select a preset.");
      return;
    }

    // 🆕 Check if user has enough credits
    if (userCredits && estimatedCost) {
      if (userCredits.credits < parseFloat(estimatedCost.credits)) {
        setError(
          `Insufficient credits. You have ${userCredits.credits.toFixed(2)} credits but need approximately ${estimatedCost.credits} credits.`
        );
        return;
      }
    }

    setLoading(true);
    setError(null);
    setUsageStats(null);
    setProcessingStage("Extracting intent and analyzing screens...");

    try {
      const res = await fetch(
        `${import.meta.env.VITE_API_BASE_URL}/generate_pipeline`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ 
            prompt: finalPrompt,
            user_id: userId  // 🆕 Send user ID
          }),
        }
      );

      if (!res.ok) {
        const errorData = await res.json();
        
        // 🆕 Handle insufficient credits error
        if (res.status === 402) {
          setError(
            `Insufficient credits. You need ${errorData.details?.required_credits?.toFixed(2)} credits but have ${errorData.details?.current_credits?.toFixed(2)} credits.`
          );
          return;
        }
        
        throw new Error(errorData.error || `Server error: ${res.status}`);
      }

      setProcessingStage("Generating component model...");
      const data = await res.json();

      setProcessingStage("Generating React Native code and preview...");

      console.log("[DEBUG] Backend response:", data);

      setLayout(data?.web_preview || data?.component_model);
      setRnCode(data?.react_native_code || {});

      // 🆕 Store usage statistics
      if (data.usage) {
        setUsageStats(data.usage);
        
        // Refresh credit balance
        await fetchUserCredits();
      }

      if (data?.react_native_code && Object.keys(data.react_native_code).length > 0) {
        setShowCode(true);
      }

      setProcessingStage("Complete!");
      setTimeout(() => setProcessingStage(""), 3000);
    } catch (e) {
      console.error("Generation error:", e);
      setError(e.message || "Generation failed. Please try again.");
      setProcessingStage("");
    } finally {
      setLoading(false);
    }
  };

  const toggleCodeView = () => setShowCode((prev) => !prev);

  const handlePresetSelect = (presetId) => {
    setSelectedPreset(presetId);
    const preset = getPresetById(presetId);
    if (preset) {
      setPrompt(preset.prompt);
    }
  };

  const screenCount = layout?.screens?.length || 0;
  const fileCount = rnCode ? Object.keys(rnCode).length : 0;

  return (
    <div className="app-container">
      {/* 🆕 Credits Header Bar */}
      <div className="credits-header">
        <div className="credits-info">
          {userCredits ? (
            <>
              <div className="credit-badge">
                <span className="credit-icon">💳</span>
                <span className="credit-amount">
                  {userCredits.credits.toFixed(2)} Credits
                </span>
              </div>
              <div className="token-info">
                <span className="token-icon">🔢</span>
                <span className="token-amount">
                  {new Intl.NumberFormat().format(userCredits.tokens_remaining)} tokens
                </span>
              </div>
            </>
          ) : (
            <div className="loading-credits">Loading balance...</div>
          )}
        </div>
        
        <a 
          href="/pricing" 
          className="buy-credits-btn"
        >
          ➕ Buy More Credits
        </a>
      </div>

      {/* 🆕 Low Credits Warning */}
      {showLowCreditsWarning && userCredits && userCredits.credits < 10 && (
        <div className="warning-banner">
          <span className="warning-icon">⚠️</span>
          <span className="warning-text">
            Low credits! You have {userCredits.credits.toFixed(2)} credits remaining.
          </span>
          <a href="/pricing" className="warning-link">
            Buy More →
          </a>
          <button 
            onClick={() => setShowLowCreditsWarning(false)}
            className="warning-close"
          >
            ✕
          </button>
        </div>
      )}

      {/* Input Section */}
      <section className="input-section">
        <div className="input-card">
          {/* Input Mode Toggle */}
          <div className="input-mode-toggle">
            <button
              onClick={() => setInputMode("manual")}
              className={`mode-btn ${inputMode === "manual" ? "active" : ""}`}
            >
              ✏️ Write Prompt
            </button>
            <button
              onClick={() => setInputMode("preset")}
              className={`mode-btn ${inputMode === "preset" ? "active" : ""}`}
            >
              📋 Use Preset
            </button>
          </div>

          {/* Manual Input Mode */}
          {inputMode === "manual" && (
            <>
              <label className="input-label">
                Describe your mobile UI (be specific for better results):
              </label>
              <textarea
                className="prompt-input"
                rows={4}
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                disabled={loading || enhancing}
                placeholder="E.g., Modern e-commerce app with product grid, search bar, and floating cart button in orange theme"
              />
              
              {/* 🆕 Estimated Cost Display */}
              {estimatedCost && (
                <div className="cost-estimate">
                  <span className="estimate-icon">📊</span>
                  <span className="estimate-text">
                    Estimated: ~{estimatedCost.credits} credits 
                    ({new Intl.NumberFormat().format(estimatedCost.tokens)} tokens)
                  </span>
                </div>
              )}

              {enhancedPrompt && (
                <div className="enhancement-badge">
                  Prompt enhanced!
                </div>
              )}

              <div className="button-group">
                <button
                  onClick={enhancePrompt}
                  className="btn-secondary"
                  disabled={enhancing || loading || !prompt.trim()}
                >
                  {enhancing ? (
                    <>
                      <span className="spinner-small"></span>
                      Enhancing...
                    </>
                  ) : (
                    <>✨ Enhance Prompt</>
                  )}
                </button>

                <button
                  onClick={generate}
                  className="btn-primary"
                  disabled={loading || enhancing}
                >
                  {loading ? (
                    <>
                      <span className="spinner"></span>
                      Generating...
                    </>
                  ) : (
                    "Generate UI"
                  )}
                </button>

                {layout && (
                  <button onClick={toggleCodeView} className="btn-secondary">
                    {showCode ? "Show Preview" : "Show Code"}
                  </button>
                )}

                {rnCode && Object.keys(rnCode).length > 0 && (
                  <ExportButton rnCode={rnCode} />
                )}
              </div>

              <p className="input-hint">
                Try: Login & Signup with social auth · E-commerce grid + cart ·
                Dashboard with sidebar
              </p>
            </>
          )}

          {/* Preset Selection Mode */}
          {inputMode === "preset" && (
            <>
              <label className="input-label">Choose a preset UI pattern:</label>

              <PresetSelector
                selectedPreset={selectedPreset}
                onSelectPreset={handlePresetSelect}
              />

              <div className="button-group">
                <button
                  onClick={generate}
                  className="btn-primary"
                  disabled={loading || !selectedPreset}
                >
                  {loading ? (
                    <>
                      <span className="spinner"></span>
                      Generating...
                    </>
                  ) : (
                    "Generate UI"
                  )}
                </button>

                {layout && (
                  <button onClick={toggleCodeView} className="btn-secondary">
                    {showCode ? "Show Preview" : "Show Code"}
                  </button>
                )}

                {rnCode && Object.keys(rnCode).length > 0 && (
                  <ExportButton rnCode={rnCode} />
                )}
              </div>

              <p className="input-hint">
                💡 Tip: You can switch to "Write Prompt" mode to edit the
                selected preset
              </p>
            </>
          )}

          {/* Processing Stage */}
          {processingStage && (
            <div className="processing-stage">
              <span className="stage-icon">⚙️</span>
              <span className="stage-text">{processingStage}</span>
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="error-message">
              <span className="error-icon">⚠️</span>
              {error}
            </div>
          )}

          {/* 🆕 Usage Statistics */}
          {usageStats && (
            <div className="usage-stats">
              <h4 className="stats-title">Generation Complete!</h4>
              <div className="stats-grid">
                <div className="stat-item">
                  <span className="stat-label">Tokens Used:</span>
                  <span className="stat-value">
                    {new Intl.NumberFormat().format(usageStats.tokens.total_tokens)}
                  </span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">Credits Deducted:</span>
                  <span className="stat-value">
                    {usageStats.credits.credits_deducted?.toFixed(4) || "N/A"}
                  </span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">Remaining Credits:</span>
                  <span className="stat-value">
                    {usageStats.credits.remaining_credits?.toFixed(2) || "N/A"}
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>
      </section>

      {/* Main Content */}
      <div className="content-layout">
        {!showCode ? (
          <section className="preview-section full-view">
            {layout ? (
              <>
                <div className="section-header">
                  <h2 className="section-title">Live Preview</h2>
                  {screenCount > 0 && (
                    <span className="screen-count">
                      {screenCount} screen{screenCount > 1 ? "s" : ""}
                    </span>
                  )}
                </div>
                <CanvasRendererLite layout={layout} />
              </>
            ) : (
              <div className="empty-state">
                <div className="empty-icon">🎨</div>
                <h3 className="empty-title">No UI Generated Yet</h3>
                <p className="empty-text">
                  Enter a prompt or select a preset, then click "Generate UI" to
                  see your app come to life!
                </p>
              </div>
            )}
          </section>
        ) : (
          <>
            <section className="preview-section split-view">
              {layout ? (
                <>
                  <div className="section-header">
                    <h2 className="section-title">Live Preview</h2>
                    {screenCount > 0 && (
                      <span className="screen-count">
                        {screenCount} screen{screenCount > 1 ? "s" : ""}
                      </span>
                    )}
                  </div>
                  <CanvasRendererLite layout={layout} />
                </>
              ) : (
                <div className="empty-state">
                  <div className="empty-icon">📱</div>
                  <h3 className="empty-title">No Preview Available</h3>
                </div>
              )}
            </section>

            <section className="code-section">
              <div className="section-header">
                <h2 className="section-title">React Native Code</h2>
                {fileCount > 0 && (
                  <span className="file-count">
                    {fileCount} file{fileCount > 1 ? "s" : ""}
                  </span>
                )}
              </div>
              {rnCode && Object.keys(rnCode).length > 0 ? (
                <CodePreview rnCode={rnCode} />
              ) : (
                <div className="empty-state">
                  <div className="empty-icon">📄</div>
                  <h3 className="empty-title">No Code Generated</h3>
                </div>
              )}
            </section>
          </>
        )}
      </div>
    </div>
  );
}