// frontend/src/components/InsufficientCreditsModal.jsx
import React from 'react';

export default function InsufficientCreditsModal({ isOpen, onClose, required, current }) {
  if (!isOpen) return null;

  return (
    <div className="credits-modal-overlay">
      <div className="credits-modal">
        <div className="modal-icon">💳</div>
        <h2 className="modal-title">Insufficient Credits</h2>
        <p className="modal-message">
          You need <strong>{required?.toFixed(2)}</strong> credits but only have{' '}
          <strong>{current?.toFixed(2)}</strong> credits.
        </p>
        
        <div className="modal-actions">
          <button 
            className="modal-btn modal-btn-primary"
            onClick={() => window.location.href = '/pricing'}
          >
            Buy Credits
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