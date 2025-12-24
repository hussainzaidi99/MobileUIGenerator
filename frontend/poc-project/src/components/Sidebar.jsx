// frontend/poc-project/src/components/Sidebar.jsx
import React, { useState, useEffect } from 'react';
import DeleteConfirmationModal from './DeleteConfirmationModal';

export default function Sidebar({
    userId,
    activeSessionId,
    onSelectConversation,
    onNewProject,
    apiBaseUrl,
    onClose
}) {
    const [conversations, setConversations] = useState([]);
    const [loading, setLoading] = useState(false);
    const [deleteModal, setDeleteModal] = useState({ isOpen: false, convId: null, title: '' });

    useEffect(() => {
        if (userId) {
            fetchConversations();
        }
    }, [userId, activeSessionId]);

    const fetchConversations = async () => {
        setLoading(true);
        try {
            const res = await fetch(`${apiBaseUrl}/conversations/list/${userId}`);
            if (res.ok) {
                const data = await res.json();
                setConversations(data.conversations || []);
            }
        } catch (err) {
            console.error("Failed to fetch history:", err);
        } finally {
            setLoading(false);
        }
    };

    const handleDeleteRequest = (e, conv) => {
        e.stopPropagation();
        setDeleteModal({
            isOpen: true,
            convId: conv.conversation_id,
            title: conv.title || "Untitled Project"
        });
    };

    const handleConfirmDelete = async () => {
        const { convId } = deleteModal;
        setDeleteModal({ isOpen: false, convId: null, title: '' });

        try {
            const res = await fetch(`${apiBaseUrl}/conversations/${convId}?user_id=${userId}`, {
                method: 'DELETE'
            });
            if (res.ok) {
                setConversations(prev => prev.filter(c => c.conversation_id !== convId));
                if (activeSessionId === convId) {
                    onNewProject();
                }
            }
        } catch (err) {
            console.error("Delete failed:", err);
        }
    };

    const formatDate = (dateStr) => {
        const date = new Date(dateStr);
        const now = new Date();
        const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24));

        if (diffDays === 0) return 'Today';
        if (diffDays === 1) return 'Yesterday';
        if (diffDays < 7) return 'Last 7 Days';
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    };

    const grouped = conversations.reduce((acc, conv) => {
        const label = formatDate(conv.last_modified);
        if (!acc[label]) acc[label] = [];
        acc[label].push(conv);
        return acc;
    }, {});

    return (
        <div className="stitch-history-sidebar">
            <div className="sidebar-new-chat">
                <button onClick={() => { onNewProject(); onClose?.(); }} className="new-chat-full-btn">
                    <span className="plus-icon">+</span> New Project
                </button>
            </div>

            <div className="sidebar-scroll-area">
                {loading && <div className="sidebar-loading">Loading history...</div>}
                {!loading && conversations.length === 0 && (
                    <div className="sidebar-empty">No previous projects</div>
                )}

                {Object.entries(grouped).map(([label, items]) => (
                    <div key={label} className="sidebar-group">
                        <h3 className="sidebar-group-label">{label}</h3>
                        {items.map(conv => (
                            <div
                                key={conv.conversation_id}
                                loading="lazy"
                                className={`sidebar-item ${activeSessionId === conv.conversation_id ? 'active' : ''}`}
                                onClick={() => { onSelectConversation(conv.conversation_id); onClose?.(); }}
                            >
                                <div className="item-icon">📱</div>
                                <div className="item-details">
                                    <div className="item-title">{conv.title || "Untitled Project"}</div>
                                    <div className="item-meta">{conv.screen_type} • {conv.version_count} v</div>
                                </div>
                                <button
                                    className="item-delete-btn"
                                    onClick={(e) => handleDeleteRequest(e, conv)}
                                >
                                    ×
                                </button>
                            </div>
                        ))}
                    </div>
                ))}
            </div>

            <DeleteConfirmationModal
                isOpen={deleteModal.isOpen}
                title={deleteModal.title}
                onConfirm={handleConfirmDelete}
                onCancel={() => setDeleteModal({ isOpen: false, convId: null, title: '' })}
            />
        </div>
    );
}
