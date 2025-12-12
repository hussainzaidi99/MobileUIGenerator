// frontend/src/components/FreeTierFullModal.jsx
import React from 'react';

export default function FreeTierFullModal({ isOpen, onClose }) {
  if (!isOpen) return null;

  return (
    <div className="credits-modal-overlay">
      <div className="credits-modal">
        <div className="modal-icon">⚠️</div>
        <h2 className="modal-title">Free Tier is Full</h2>
        <p className="modal-message">
          We've reached our 20 free-tier user limit. 
          Please purchase a plan to get started with unlimited access!
        </p>
        
        <div className="modal-actions">
          <button 
            className="modal-btn modal-btn-primary"
            onClick={() => window.location.href = '/pricing'}
          >
            View Plans
          </button>
          <button 
            className="modal-btn modal-btn-secondary"
            onClick={onClose}
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}