import React from 'react';

const DeleteConfirmationModal = ({ isOpen, onConfirm, onCancel, title }) => {
    if (!isOpen) return null;

    return (
        <div className="stitch-modal-overlay" onClick={onCancel}>
            <div
                className="stitch-modal-content"
                onClick={(e) => e.stopPropagation()}
            >
                <div className="stitch-modal-icon">🗑️</div>
                <h2 className="stitch-modal-title">Delete Conversation?</h2>
                <p className="stitch-modal-description">
                    Are you sure you want to delete <strong>"{title}"</strong>?
                    This action cannot be undone and all history will be lost.
                </p>
                <div className="stitch-modal-actions">
                    <button
                        className="btn-modal-cancel"
                        onClick={onCancel}
                    >
                        Go Back
                    </button>
                    <button
                        className="btn-modal-delete"
                        onClick={onConfirm}
                    >
                        Yes, Delete
                    </button>
                </div>
            </div>
        </div>
    );
};

export default DeleteConfirmationModal;
