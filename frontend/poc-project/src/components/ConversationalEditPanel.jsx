// frontend/poc-project/src/components/ConversationalEditPanel.jsx
// Drop-in component for live editing within existing App.jsx

import React, { useState, useRef, useEffect } from 'react';

/**
 * Conversational Edit Panel
 * 
 * Allows users to make live edits to generated UI using natural language.
 * Maintains conversation context with the LLM for iterative refinement.
 * 
 * Usage in App.jsx:
 * {layout && sessionId && (
 *   <ConversationalEditPanel
 *     sessionId={sessionId}
 *     userId={user?.id}
 *     onLayoutUpdate={(newLayout) => setLayout(newLayout)}
 *     apiBaseUrl={import.meta.env.VITE_API_BASE_URL}
 *   />
 * )}
 */
export default function ConversationalEditPanel({ 
  sessionId, 
  userId,
  onLayoutUpdate,
  apiBaseUrl = import.meta.env.VITE_API_BASE_URL
}) {
  const [editPrompt, setEditPrompt] = useState('');
  const [isEditing, setIsEditing] = useState(false);
  const [editHistory, setEditHistory] = useState([]);
  const [error, setError] = useState(null);
  const [collapsed, setCollapsed] = useState(false);
  const [stats, setStats] = useState({ editCount: 0, tokensUsed: 0 });
  
  const textareaRef = useRef(null);

  // Auto-focus textarea when panel opens
  useEffect(() => {
    if (!collapsed && textareaRef.current) {
      textareaRef.current.focus();
    }
  }, [collapsed]);

  const handleEdit = async () => {
    if (!editPrompt.trim()) return;
    
    setIsEditing(true);
    setError(null);

    try {
      const response = await fetch(`${apiBaseUrl}/edit-component-model`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          user_id: userId,
          prompt: editPrompt.trim()
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        
        // Handle insufficient credits
        if (response.status === 402) {
          setError(`Insufficient credits: ${errorData.details?.message || 'Please top up'}`);
          return;
        }
        
        throw new Error(errorData.error || `Error: ${response.status}`);
      }

      const data = await response.json();

      // Update layout in parent component
      if (data.web_preview) {
        onLayoutUpdate(data.web_preview);
      }

      // Add to history
      setEditHistory(prev => [
        ...prev,
        {
          prompt: editPrompt,
          timestamp: new Date().toISOString(),
          success: true
        }
      ]);

      // Update stats
      setStats({
        editCount: data.edit_count || stats.editCount + 1,
        tokensUsed: stats.tokensUsed + (data.usage?.tokens?.total_tokens || 0)
      });

      // Clear input
      setEditPrompt('');
      
    } catch (err) {
      console.error('Edit error:', err);
      setError(err.message || 'Failed to apply edit');
      
      // Add failed edit to history
      setEditHistory(prev => [
        ...prev,
        {
          prompt: editPrompt,
          timestamp: new Date().toISOString(),
          success: false,
          error: err.message
        }
      ]);
    } finally {
      setIsEditing(false);
    }
  };

  const handleKeyDown = (e) => {
    // Submit on Ctrl/Cmd + Enter
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      handleEdit();
    }
  };

  if (collapsed) {
    return (
      <div className="edit-panel-collapsed">
        <button
          onClick={() => setCollapsed(false)}
          className="stitch-btn stitch-btn-secondary"
          style={{ width: '100%' }}
          title="Open edit panel"
        >
          <span style={{ fontSize: '16px' }}>✏️</span>
          Edit Live
          {stats.editCount > 0 && (
            <span style={{ 
              marginLeft: '8px', 
              background: 'rgba(59, 130, 246, 0.2)',
              padding: '2px 8px',
              borderRadius: '12px',
              fontSize: '11px'
            }}>
              {stats.editCount} edit{stats.editCount > 1 ? 's' : ''}
            </span>
          )}
        </button>
      </div>
    );
  }

  return (
    <div className="edit-panel-container">
      {/* Header */}
      <div className="edit-panel-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '18px' }}>💬</span>
          <div>
            <div style={{ 
              fontSize: '14px', 
              fontWeight: '600',
              color: '#0F172A'
            }}>
              Live Edit
            </div>
            <div style={{ 
              fontSize: '11px', 
              color: '#64748B',
              marginTop: '2px'
            }}>
              Make changes with natural language
            </div>
          </div>
        </div>
        
        <button
          onClick={() => setCollapsed(true)}
          className="collapse-button"
          title="Collapse panel"
        >
          ✕
        </button>
      </div>

      {/* Stats */}
      {stats.editCount > 0 && (
        <div className="edit-stats">
          <div className="stat-item">
            <span className="stat-label">Edits:</span>
            <span className="stat-value">{stats.editCount}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Tokens:</span>
            <span className="stat-value">{stats.tokensUsed.toLocaleString()}</span>
          </div>
        </div>
      )}

      {/* History (recent 3) */}
      {editHistory.length > 0 && (
        <div className="edit-history">
          <div className="history-label">Recent edits:</div>
          {editHistory.slice(-3).reverse().map((edit, idx) => (
            <div 
              key={idx} 
              className={`history-item ${edit.success ? 'success' : 'error'}`}
            >
              <span className="history-icon">
                {edit.success ? '✓' : '✗'}
              </span>
              <span className="history-text">
                {edit.prompt.length > 40 
                  ? edit.prompt.substring(0, 40) + '...' 
                  : edit.prompt}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Input Area */}
      <div className="edit-input-section">
        <textarea
          ref={textareaRef}
          value={editPrompt}
          onChange={(e) => setEditPrompt(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Describe what you want to change...&#10;&#10;Examples:&#10;• Change login button to green&#10;• Add a forgot password link&#10;• Make the header text larger&#10;• Remove the subtitle"
          className="edit-textarea"
          rows={4}
          disabled={isEditing}
        />
        
        <button
          onClick={handleEdit}
          disabled={isEditing || !editPrompt.trim()}
          className="edit-submit-button"
        >
          {isEditing ? (
            <>
              <span className="spinner-small"></span>
              Applying...
            </>
          ) : (
            <>
              Apply Changes
              <span style={{ marginLeft: '8px' }}>→</span>
            </>
          )}
        </button>

        <div className="edit-hint">
          Press <kbd>Ctrl</kbd> + <kbd>Enter</kbd> to submit
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="edit-error">
          <span className="error-icon">⚠️</span>
          <span>{error}</span>
        </div>
      )}

      {/* Example Prompts */}
      {editHistory.length === 0 && (
        <div className="example-prompts">
          <div className="example-label">Try these:</div>
          {[
            "Change the button color to blue",
            "Add a loading spinner",
            "Make the title bold and larger",
            "Add spacing between components"
          ].map((example, idx) => (
            <button
              key={idx}
              onClick={() => setEditPrompt(example)}
              className="example-chip"
              disabled={isEditing}
            >
              {example}
            </button>
          ))}
        </div>
      )}

      <style jsx>{`
        .edit-panel-container {
          background: white;
          border-radius: 16px;
          padding: 20px;
          box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08);
          border: 1px solid #E2E8F0;
          margin-top: 20px;
          animation: slideIn 0.3s ease-out;
        }

        @keyframes slideIn {
          from {
            opacity: 0;
            transform: translateY(-10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .edit-panel-collapsed {
          margin-top: 20px;
        }

        .edit-panel-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 16px;
          padding-bottom: 16px;
          border-bottom: 1px solid #E2E8F0;
        }

        .collapse-button {
          background: transparent;
          border: none;
          color: #64748B;
          cursor: pointer;
          font-size: 20px;
          padding: 4px 8px;
          border-radius: 6px;
          transition: all 0.2s;
        }

        .collapse-button:hover {
          background: #F1F5F9;
          color: #0F172A;
        }

        .edit-stats {
          display: flex;
          gap: 16px;
          margin-bottom: 16px;
          padding: 12px;
          background: #F8FAFC;
          border-radius: 8px;
        }

        .stat-item {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 13px;
        }

        .stat-label {
          color: #64748B;
          font-weight: 500;
        }

        .stat-value {
          color: #0F172A;
          font-weight: 700;
        }

        .edit-history {
          margin-bottom: 16px;
        }

        .history-label {
          font-size: 11px;
          color: #64748B;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.5px;
          margin-bottom: 8px;
        }

        .history-item {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 8px 12px;
          margin-bottom: 6px;
          border-radius: 8px;
          font-size: 13px;
          transition: all 0.2s;
        }

        .history-item.success {
          background: rgba(16, 185, 129, 0.08);
          color: #059669;
        }

        .history-item.error {
          background: rgba(239, 68, 68, 0.08);
          color: #DC2626;
        }

        .history-icon {
          font-weight: bold;
          font-size: 14px;
        }

        .history-text {
          flex: 1;
          font-size: 12px;
        }

        .edit-input-section {
          margin-bottom: 16px;
        }

        .edit-textarea {
          width: 100%;
          padding: 14px;
          border: 2px solid #E2E8F0;
          border-radius: 12px;
          font-size: 14px;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
          resize: vertical;
          transition: all 0.2s;
          margin-bottom: 12px;
        }

        .edit-textarea:focus {
          outline: none;
          border-color: #3B82F6;
          box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        }

        .edit-textarea:disabled {
          background: #F8FAFC;
          cursor: not-allowed;
        }

        .edit-textarea::placeholder {
          color: #94A3B8;
        }

        .edit-submit-button {
          width: 100%;
          padding: 14px;
          background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%);
          color: white;
          border: none;
          border-radius: 12px;
          font-size: 14px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
        }

        .edit-submit-button:hover:not(:disabled) {
          transform: translateY(-1px);
          box-shadow: 0 8px 20px rgba(59, 130, 246, 0.3);
        }

        .edit-submit-button:active:not(:disabled) {
          transform: translateY(0);
        }

        .edit-submit-button:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .edit-hint {
          text-align: center;
          font-size: 11px;
          color: #94A3B8;
          margin-top: 8px;
        }

        .edit-hint kbd {
          background: #F1F5F9;
          border: 1px solid #CBD5E1;
          border-radius: 4px;
          padding: 2px 6px;
          font-family: monospace;
          font-size: 10px;
        }

        .edit-error {
          background: #FEF2F2;
          border: 1px solid #FECACA;
          color: #DC2626;
          padding: 12px 14px;
          border-radius: 8px;
          font-size: 13px;
          display: flex;
          align-items: center;
          gap: 8px;
          margin-top: 12px;
        }

        .error-icon {
          font-size: 16px;
        }

        .example-prompts {
          margin-top: 16px;
          padding-top: 16px;
          border-top: 1px solid #E2E8F0;
        }

        .example-label {
          font-size: 11px;
          color: #64748B;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.5px;
          margin-bottom: 10px;
        }

        .example-chip {
          display: inline-block;
          background: #F8FAFC;
          border: 1px solid #E2E8F0;
          color: #475569;
          padding: 6px 12px;
          border-radius: 8px;
          font-size: 12px;
          cursor: pointer;
          transition: all 0.2s;
          margin-right: 8px;
          margin-bottom: 8px;
        }

        .example-chip:hover:not(:disabled) {
          background: #EFF6FF;
          border-color: #93C5FD;
          color: #1E40AF;
        }

        .example-chip:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .spinner-small {
          width: 14px;
          height: 14px;
          border: 2px solid rgba(255, 255, 255, 0.3);
          border-top-color: white;
          border-radius: 50%;
          animation: spin 0.6s linear infinite;
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}