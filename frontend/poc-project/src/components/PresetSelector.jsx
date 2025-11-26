// frontend/src/components/PresetSelector.jsx
import React, { useState } from "react";
import { PRESET_PROMPTS, PRESET_CATEGORIES, getPresetsByCategory } from "../constants/presetPrompts";

export default function PresetSelector({ selectedPreset, onSelectPreset }) {
  const [activeCategory, setActiveCategory] = useState("Authentication");

  return (
    <div className="preset-selector">
      {/* Category Tabs */}
      <div className="preset-categories">
        {PRESET_CATEGORIES.map((category) => (
          <button
            key={category}
            onClick={() => setActiveCategory(category)}
            className={`category-tab ${activeCategory === category ? "active" : ""}`}
          >
            {category}
          </button>
        ))}
      </div>

      {/* Preset Grid */}
      <div className="preset-grid">
        {getPresetsByCategory(activeCategory).map((preset) => (
          <label
            key={preset.id}
            className={`preset-card ${selectedPreset === preset.id ? "selected" : ""}`}
          >
            <input
              type="radio"
              name="preset"
              value={preset.id}
              checked={selectedPreset === preset.id}
              onChange={() => onSelectPreset(preset.id)}
              className="preset-radio"
            />
            <div className="preset-icon">{preset.icon}</div>
            <div className="preset-label">{preset.label}</div>
          </label>
        ))}
      </div>

      {/* Selected Prompt Preview */}
      {selectedPreset && (
        <div className="preset-preview">
          <span className="preview-label">Selected:</span>
          <p className="preview-text">
            {PRESET_PROMPTS.find(p => p.id === selectedPreset)?.label}
          </p>
        </div>
      )}
    </div>
  );
}