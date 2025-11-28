// frontend/src/App.jsx - WITH PRESET PROMPTS
import React, { useState } from "react";
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
  const [prompt, setPrompt] = useState("Modern login and signup screens with social auth");
  const [error, setError] = useState(null);
  const [showCode, setShowCode] = useState(false);
  const [processingStage, setProcessingStage] = useState("");
  const [enhancedPrompt, setEnhancedPrompt] = useState("");
  const [enhancing, setEnhancing] = useState(false);
  
  // NEW: Preset state
  const [inputMode, setInputMode] = useState("manual"); // "manual" or "preset"
  const [selectedPreset, setSelectedPreset] = useState(null);

  const enhancePrompt = async () => {
    if (!prompt.trim()) return;

    setEnhancing(true);
    setError(null);

    try {
      const res = await fetch("http://127.0.0.1:8005/refine", {
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
    // Get final prompt (from preset or manual input)
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

    setLoading(true);
    setError(null);
    setProcessingStage("Extracting intent and analyzing screens...");

    try {
      const res = await fetch("http://127.0.0.1:8005/generate_pipeline", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: finalPrompt }),
      });

      if (!res.ok) {
        const text = await res.text();
        throw new Error(`Server error: ${res.status} ${text}`);
      }

      setProcessingStage("Generating component model...");
      const data = await res.json();

      setProcessingStage("Generating React Native code and preview...");

      console.log("[DEBUG] Backend response:", data);

      setLayout(data?.web_preview || data?.component_model);
      setRnCode(data?.react_native_code || {});

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

  const toggleCodeView = () => setShowCode(!showCode);

  // NEW: Handle preset selection
  const handlePresetSelect = (presetId) => {
    setSelectedPreset(presetId);
    const preset = getPresetById(presetId);
    if (preset) {
      setPrompt(preset.prompt); // Auto-fill textarea
    }
  };

  const screenCount = layout?.screens?.length || 0;
  const fileCount = rnCode ? Object.keys(rnCode).length : 0;
  const originalWordCount = prompt.trim().split(/\s+/).filter(Boolean).length;
  const enhancedWordCount = enhancedPrompt ? enhancedPrompt.trim().split(/\s+/).filter(Boolean).length : 0;

  return (
    <div className="app-container">
      {/* Header */}
      <header className="app-header">
        <div className="header-content">
          <h1 className="app-title">Mobile UI Generator</h1>
          <p className="app-subtitle">AI-Powered Mobile User Interfaces Generator</p>
        </div>
      </header>

      {/* Input Section */}
      <section className="input-section">
        <div className="input-card">
          {/* NEW: Input Mode Toggle */}
          <div className="input-mode-toggle">
            <button
              onClick={() => setInputMode("manual")}
              className={`mode-btn ${inputMode === "manual" ? "active" : ""}`}
            >
              ✍️ Write Prompt
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

              {/* Enhancement Feedback */}
              {enhancedPrompt && enhancedWordCount > originalWordCount && (
                <div className="enhancement-badge">
                  Prompt enhanced! (+{enhancedWordCount - originalWordCount} words)
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

                {rnCode && Object.keys(rnCode).length > 0 && <ExportButton rnCode={rnCode} />}
              </div>

              <p className="input-hint">
                Try: Login & Signup with social auth · E-commerce grid + cart · Dashboard with sidebar
              </p>
            </>
          )}

          {/* NEW: Preset Selection Mode */}
          {inputMode === "preset" && (
            <>
              <label className="input-label">
                Choose a preset UI pattern:
              </label>
              
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

                {rnCode && Object.keys(rnCode).length > 0 && <ExportButton rnCode={rnCode} />}
              </div>

              <p className="input-hint">
                💡 Tip: You can switch to "Write Prompt" mode to edit the selected preset
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
                  Enter a prompt or select a preset, then click "Generate UI" to see your app come to life!
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