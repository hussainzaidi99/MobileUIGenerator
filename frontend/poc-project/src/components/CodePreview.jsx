// frontend/src/components/CodePreview.jsx - React Native Edition
import React, { useState } from "react";

export default function CodePreview({ rnCode }) {  // ✅ RENAMED PROP
  const [selectedFile, setSelectedFile] = useState(null);
  const [copied, setCopied] = useState(false);

  const files = Object.entries(rnCode || {});

  // Auto-select first file
  React.useEffect(() => {
    if (files.length > 0 && !selectedFile) {
      setSelectedFile(files[0][0]);
    }
  }, [rnCode]);  // ✅ FIXED DEPENDENCY

  const currentCode = selectedFile ? rnCode[selectedFile] : "";

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(currentCode);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Copy failed:", err);
    }
  };

  const getFileIcon = (filename) => {
    if (filename.endsWith(".tsx") || filename.endsWith(".ts")) return "⚛️";
    if (filename.endsWith(".json")) return "📦";
    if (filename.endsWith(".md")) return "📖";
    return "📄";
  };

  const getFileName = (path) => {
    const parts = path.split("/");
    return parts[parts.length - 1];
  };

  if (!rnCode || files.length === 0) {
    return (
      <div className="code-preview-empty">
        <p>No code generated yet</p>
      </div>
    );
  }

  return (
    <div className="code-preview">
      {/* File Tree Sidebar */}
      <div className="file-tree">
        <div className="file-tree-header">
          <span className="file-tree-title">📂 Files</span>
        </div>
        <div className="file-list">
          {files.map(([filename]) => (
            <button
              key={filename}
              onClick={() => setSelectedFile(filename)}
              className={`file-item ${selectedFile === filename ? "active" : ""}`}
            >
              <span className="file-icon">{getFileIcon(filename)}</span>
              <span className="file-name">{getFileName(filename)}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Code Display */}
      <div className="code-display">
        <div className="code-header">
          <span className="current-file">{selectedFile}</span>
          <button
            onClick={copyToClipboard}
            className="copy-button"
            title="Copy to clipboard"
          >
            {copied ? "✓ Copied!" : "📋 Copy"}
          </button>
        </div>
        <pre className="code-content">
          <code className="language-typescript">{currentCode}</code>
        </pre>
      </div>
    </div>
  );
}