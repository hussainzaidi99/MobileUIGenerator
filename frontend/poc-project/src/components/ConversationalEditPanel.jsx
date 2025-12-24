// frontend/poc-project/src/components/ConversationalEditPanel.jsx
// ✅ FIXED: Input scrolls with conversation

import React, { useState, useRef, useEffect } from 'react';

export default function ConversationalEditPanel({
  sessionId,
  userId,
  initialPrompt,
  onLayoutUpdate,
  apiBaseUrl = import.meta.env.VITE_API_BASE_URL,
  loading = false,
  processingStage = ""
}) {
  const [prompt, setPrompt] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [messages, setMessages] = useState([]);
  const [error, setError] = useState(null);

  const textareaRef = useRef(null);
  const messagesEndRef = useRef(null);
  const containerRef = useRef(null); // NEW: Reference to scrollable container

  // Fetch history when sessionId changes
  useEffect(() => {
    if (sessionId && !loading) {
      fetchHistory();
    }
  }, [sessionId, loading]);

  const fetchHistory = async () => {
    try {
      const res = await fetch(`${apiBaseUrl}/edit-session/${sessionId}`);
      if (res.ok) {
        const data = await res.json();
        if (data.conversation_history && data.conversation_history.length > 0) {
          // Format history from backend
          const history = data.conversation_history.map((m, idx) => ({
            id: `hist-${idx}`,
            role: m.role,
            content: m.content,
            timestamp: m.timestamp
          }));
          setMessages(history);
        } else if (initialPrompt && !loading) {
          // Initial generation fallback
          setMessages([
            { id: 'init-user', role: 'user', content: initialPrompt, timestamp: new Date().toISOString() },
            { id: 'init-ai', role: 'assistant', content: "Initial UI generated. What refinement would you like?", timestamp: new Date().toISOString() }
          ]);
        }
      }
    } catch (err) {
      console.error("Failed to fetch history:", err);
    }
  };

  // ✅ IMPROVED: Smooth scroll to bottom with better timing
  useEffect(() => {
    const scrollToBottom = () => {
      if (messagesEndRef.current) {
        messagesEndRef.current.scrollIntoView({
          behavior: 'smooth',
          block: 'end'
        });
      }
    };

    // Scroll immediately
    scrollToBottom();

    // Scroll again after a short delay to ensure content is rendered
    const timeoutId = setTimeout(scrollToBottom, 100);

    return () => clearTimeout(timeoutId);
  }, [messages, isProcessing]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px';
    }
  }, [prompt]);

  const handleSendMessage = async () => {
    if (!prompt.trim() || !sessionId || isProcessing) return;

    const currentPrompt = prompt.trim();
    setPrompt('');
    setIsProcessing(true);
    setError(null);

    // Add user message
    const userMsgId = Date.now().toString();
    setMessages(prev => [...prev, {
      id: userMsgId,
      role: 'user',
      content: currentPrompt,
      timestamp: new Date().toISOString()
    }]);

    try {
      console.log("📤 Sending edit request:", {
        session_id: sessionId,
        user_id: userId,
        prompt: currentPrompt
      });

      const response = await fetch(`${apiBaseUrl}/edit-component-model`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          user_id: userId,
          prompt: currentPrompt
        })
      });

      if (!response.ok) {
        const errorData = await response.json();

        // Handle insufficient credits
        if (response.status === 402) {
          throw new Error(`Insufficient credits: ${errorData.details?.message || 'Please top up your account'}`);
        }

        throw new Error(errorData.error || `Error: ${response.status}`);
      }

      const data = await response.json();

      console.log("✅ Edit response received:", data);

      // ✅ CRITICAL FIX: Update layout with proper data structure
      if (data.web_preview) {
        console.log("🔄 Updating layout with web_preview");
        onLayoutUpdate(data.web_preview, data.react_native_code);
      } else if (data.component_model) {
        console.log("🔄 Updating layout with component_model");
        onLayoutUpdate(data.component_model, data.react_native_code);
      } else {
        console.warn("⚠️ No layout data in response");
      }

      // Add assistant success message
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        role: 'assistant',
        content: data.message || "Changes applied successfully! How does it look now?",
        timestamp: new Date().toISOString()
      }]);

    } catch (err) {
      console.error('❌ Edit error:', err);
      setError(err.message);

      // Add assistant error message
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        role: 'assistant',
        content: `I ran into an issue: ${err.message}. Please try again or rephrase your request.`,
        isError: true,
        timestamp: new Date().toISOString()
      }]);
    } finally {
      setIsProcessing(false);
      // Refocus textarea after processing
      setTimeout(() => textareaRef.current?.focus(), 100);
    }
  };

  const handleKeyDown = (e) => {
    // Submit on Enter (without Shift)
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="stitch-sub-panel" ref={containerRef}>
      {/* ✅ FIXED: Messages + Input in scrollable container */}
      <div className="stitch-conversation-wrapper">

        {/* Messages Container */}
        <div className="stitch-messages-container">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`stitch-message ${msg.role === 'user' ? 'user' : 'assistant'} ${msg.isError ? 'error' : ''}`}
            >
              <div className="message-avatar">
                {msg.role === 'user' ? '👤' : '✨'}
              </div>
              <div className="message-content">
                {msg.content}
              </div>
            </div>
          ))}

          {/* Loading indicator during initial generation */}
          {loading && (
            <div className="stitch-message assistant processing">
              <div className="message-avatar">✨</div>
              <div className="message-content">
                <div style={{ marginBottom: '4px' }}>
                  {processingStage || "Working on your request..."}
                </div>
                <span className="typing-dot">.</span>
                <span className="typing-dot">.</span>
                <span className="typing-dot">.</span>
              </div>
            </div>
          )}

          {/* Processing indicator for edits */}
          {isProcessing && !loading && (
            <div className="stitch-message assistant processing">
              <div className="message-avatar">✨</div>
              <div className="message-content">
                <span className="typing-dot">.</span>
                <span className="typing-dot">.</span>
                <span className="typing-dot">.</span>
              </div>
            </div>
          )}

          {/* ✅ IMPROVED: Input Dock - Now inside scrollable area */}
          <div className="stitch-input-dock-inline">
            <div className="stitch-dock-inner">
              <textarea
                ref={textareaRef}
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={
                  loading
                    ? "Generating... please wait"
                    : sessionId
                      ? "Type your changes here..."
                      : "Waiting for initial generation..."
                }
                className="stitch-dock-input"
                rows={1}
                disabled={isProcessing || loading || !sessionId}
              />
              <button
                onClick={handleSendMessage}
                disabled={!prompt.trim() || isProcessing || loading || !sessionId}
                className="stitch-dock-load-btn"
                title="Send message (Enter)"
              >
                {isProcessing ? '...' : '↑'}
              </button>
            </div>

            {/* Error message */}
            {error && !isProcessing && (
              <div className="stitch-mini-error">⚠️ {error}</div>
            )}

            {/* Helper text */}
            {!loading && !isProcessing && sessionId && (
              <div style={{
                fontSize: '11px',
                color: '#94A3B8',
                marginTop: '8px',
                paddingLeft: '12px'
              }}>
                Press <strong>Enter</strong> to send, <strong>Shift+Enter</strong> for new line
              </div>
            )}
          </div>

          {/* Scroll anchor */}
          <div ref={messagesEndRef} style={{ height: '1px' }} />
        </div>
      </div>
    </div>
  );
}