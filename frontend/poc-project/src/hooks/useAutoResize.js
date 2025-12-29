import { useEffect } from 'react';

/**
 * Hook to automatically resize a textarea based on its content.
 * @param {React.RefObject} ref - Reference to the textarea element.
 * @param {string} value - The current value of the textarea.
 */
export default function useAutoResize(ref, value) {
    useEffect(() => {
        if (ref.current) {
            // Reset height to auto to get the correct scrollHeight
            ref.current.style.height = 'auto';
            // Set the height based on scrollHeight
            ref.current.style.height = `${ref.current.scrollHeight}px`;
        }
    }, [ref, value]);
}
