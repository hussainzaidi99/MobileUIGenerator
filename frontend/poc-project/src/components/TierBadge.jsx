// frontend/src/components/TierBadge.jsx
import React from 'react';

const TIER_CONFIG = {
  free: {
    icon: '🆓',
    label: 'Free',
    color: '#94a3b8'
  },
  limited: {
    icon: '⚠️',
    label: 'Limited',
    color: '#f59e0b'
  },
  starter: {
    icon: '🌱',
    label: 'Starter',
    color: '#67e8f9'
  },
  pro: {
    icon: '⚡',
    label: 'Pro',
    color: '#c084fc'
  },
  enterprise: {
    icon: '👑',
    label: 'Enterprise',
    color: '#fbbf24'
  }
};

export default function TierBadge({ tier, expiresAt, daysRemaining }) {
  const config = TIER_CONFIG[tier] || TIER_CONFIG.free;
  
  // Format expiration message
  const getExpirationText = () => {
    if (!expiresAt) return null;
    
    if (daysRemaining <= 0) {
      return 'Expired';
    } else if (daysRemaining <= 7) {
      return `${daysRemaining} days left`;
    }
    return null;
  };

  const expirationText = getExpirationText();
  const isExpiringSoon = daysRemaining && daysRemaining <= 7 && daysRemaining > 0;

  return (
    <div 
      className={`tier-badge ${tier}`}
      style={{
        animation: isExpiringSoon ? 'pulse 2s ease-in-out infinite' : 'none'
      }}
    >
      <span className="tier-icon">{config.icon}</span>
      <span className="tier-label">{config.label}</span>
      {expirationText && (
        <span 
          className="tier-expiration"
          style={{
            marginLeft: '8px',
            fontSize: '11px',
            opacity: 0.8,
            color: isExpiringSoon ? '#fbbf24' : 'inherit'
          }}
        >
          ({expirationText})
        </span>
      )}
    </div>
  );
}