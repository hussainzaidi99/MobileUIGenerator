// frontend/src/components/PasswordInput.jsx
/**
 * Password input with visibility toggle
 */
import React, { useState } from 'react';

export default function PasswordInput({
    value,
    onChange,
    placeholder = "Password",
    disabled = false,
    className = "",
    ...props
}) {
    const [showPassword, setShowPassword] = useState(false);

    return (
        <div style={{ position: 'relative', width: '100%' }}>
            <input
                type={showPassword ? 'text' : 'password'}
                value={value}
                onChange={onChange}
                placeholder={placeholder}
                disabled={disabled}
                className={className}
                style={{
                    width: '100%',
                    paddingRight: '45px',
                    ...props.style
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
                    color: '#64748B',
                    fontSize: '18px',
                    padding: '4px 8px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    opacity: disabled ? 0.5 : 1,
                    transition: 'color 0.2s'
                }}
                onMouseEnter={(e) => !disabled && (e.target.style.color = '#0F172A')}
                onMouseLeave={(e) => !disabled && (e.target.style.color = '#64748B')}
                title={showPassword ? 'Hide password' : 'Show password'}
            >
                {showPassword ? '👁️' : '👁️‍🗨️'}
            </button>
        </div>
    );
}
