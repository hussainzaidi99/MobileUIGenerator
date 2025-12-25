// frontend/src/utils/toast.js
/**
 * User-friendly toast notifications using Sonner
 */
import { toast as sonnerToast } from 'sonner';

export const toast = {
    /**
     * Show success toast
     * @param {string} message - Main message
     * @param {string} description - Optional description
     */
    success: (message, description) => {
        sonnerToast.success(message, {
            description: description || undefined
        });
    },

    /**
     * Show error toast
     * @param {string} message - Main message
     * @param {string} description - Optional description
     */
    error: (message, description) => {
        sonnerToast.error(message, {
            description: description || undefined
        });
    },

    /**
     * Show info toast
     * @param {string} message - Main message
     * @param {string} description - Optional description
     */
    info: (message, description) => {
        sonnerToast.info(message, {
            description: description || undefined
        });
    },

    /**
     * Show warning toast
     * @param {string} message - Main message
     * @param {string} description - Optional description
     */
    warning: (message, description) => {
        sonnerToast.warning(message, {
            description: description || undefined
        });
    },

    /**
     * Show loading toast
     * @param {string} message - Loading message
     * @returns {string|number} Toast ID for dismissal
     */
    loading: (message) => {
        return sonnerToast.loading(message);
    },

    /**
     * Dismiss a toast by ID
     * @param {string|number} toastId - Toast ID to dismiss
     */
    dismiss: (toastId) => {
        sonnerToast.dismiss(toastId);
    },

    /**
     * Show promise toast (auto-updates based on promise state)
     * @param {Promise} promise - Promise to track
     * @param {Object} messages - Messages for loading, success, error states
     */
    promise: (promise, messages) => {
        return sonnerToast.promise(promise, messages);
    }
};
