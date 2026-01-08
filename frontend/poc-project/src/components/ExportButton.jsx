// frontend/src/components/ExportButton.jsx - React Native Edition
import React, { useState } from "react";
import { toast } from '../utils/toast';


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
    const exportToastId = toast.loading("Preparing your project export...");

    try {
      const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080';
      const response = await fetch(`${API_BASE}/export/react-native`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ react_native_code: rnCode }),
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
      toast.success("Export Complete!", "Your React Native project ZIP is ready.");
      toast.dismiss(exportToastId);
    } catch (err) {
      console.error("Export error:", err);
      setError(err.message);
      toast.error("Export Failed", err.message);
      if (typeof exportToastId !== 'undefined') toast.dismiss(exportToastId);
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
    </div>
  );
}