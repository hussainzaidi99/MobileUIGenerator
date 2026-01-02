// frontend/src/components/PasswordInput.jsx
/**
 * Password input with visibility toggle
 */
import React, { useState } from 'react';
import { Eye, EyeOff } from 'lucide-react';

export default function PasswordInput({
    value,
    onChange,
    placeholder = "Password",
    disabled = false,
    className = "",
    inputStyle = {},
    containerStyle = {},
    ...props
}) {
    const [showPassword, setShowPassword] = useState(false);

    return (
        <div style={{ position: 'relative', width: '100%', ...containerStyle }}>
            <input
                type={showPassword ? 'text' : 'password'}
                value={value}
                onChange={onChange}
                placeholder={placeholder}
                disabled={disabled}
                className={className}
                style={{
                    width: '100%',
                    padding: '12px 16px',
                    paddingRight: '45px',
                    background: 'rgba(30, 41, 59, 0.6)',
                    border: '2px solid rgba(255, 255, 255, 0.1)',
                    borderRadius: '12px',
                    color: '#f8fafc',
                    fontSize: '14px',
                    outline: 'none',
                    transition: 'all 0.2s',
                    boxSizing: 'border-box',
                    ...inputStyle
                }}
                onFocus={(e) => {
                    e.target.style.borderColor = "#6366f1";
                    e.target.style.boxShadow = "0 0 0 4px rgba(99, 102, 241, 0.2)";
                }}
                onBlur={(e) => {
                    e.target.style.borderColor = "rgba(255, 255, 255, 0.1)";
                    e.target.style.boxShadow = "none";
                }}
                {...props}
            />
            <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                disabled={disabled}
                style={{
                    position: 'absolute',
                    right: '12px',
                    top: '50%',
                    transform: 'translateY(-50%)',
                    background: 'none',
                    border: 'none',
                    cursor: disabled ? 'not-allowed' : 'pointer',
                    color: '#94a3b8',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    opacity: disabled ? 0.5 : 1,
                    transition: 'all 0.2s',
                    padding: '8px',
                    zIndex: 2
                }}
                onMouseEnter={(e) => !disabled && (e.currentTarget.style.color = '#f8fafc')}
                onMouseLeave={(e) => !disabled && (e.currentTarget.style.color = '#94a3b8')}
                title={showPassword ? 'Hide password' : 'Show password'}
            >
                {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
            </button>
        </div>
    );
}
