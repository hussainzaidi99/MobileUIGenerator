// frontend/src/components/ExportButton.jsx - React Native Edition
import React, { useState } from "react";

export default function ExportButton({ rnCode }) {  // ✅ RENAMED PROP
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState(null);

  const handleExport = async () => {
    if (!rnCode || Object.keys(rnCode).length === 0) {
      setError("No code to export");
      return;
    }

    setExporting(true);
    setError(null);

    try {
      // ✅ FIX: Use correct endpoint and payload key
      const response = await fetch("http://127.0.0.1:8000/export/react-native", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ react_native_code: rnCode }),  // ✅ FIXED KEY
      });

      if (!response.ok) {
        throw new Error(`Export failed: ${response.statusText}`);
      }

      // Download the ZIP file
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `react_native_app_${Date.now()}.zip`;  // ✅ FIXED FILENAME
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      console.log("✅ Export successful");
    } catch (err) {
      console.error("Export error:", err);
      setError(err.message);
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="export-button-container">
      <button
        onClick={handleExport}
        className="btn-export"
        disabled={exporting || !rnCode}
        title="Download React Native project as ZIP"
      >
        {exporting ? (
          <>
            <span className="spinner-small"></span>
            Exporting...
          </>
        ) : (
          <>
            <span className="download-icon">⬇️</span>
            Export React Native
          </>
        )}
      </button>
      {error && (
        <div className="export-error">
          <span className="error-icon-small">⚠️</span>
          {error}
        </div>
      )}
    </div>
  );
}