// src/components/backgrounds/DarkVeil.jsx
// Animated dark veil background inspired by reactbits.dev
// Optimized for performance with conditional rendering

import React, { useMemo } from 'react';
import './DarkVeil.css';

export default function DarkVeil({ 
  opacity = 0.3,
  particleCount = 50,
  enableAnimation = true,
  showMesh = true 
}) {
  // Generate particle positions once (memoized)
  const particles = useMemo(() => {
    return Array.from({ length: particleCount }).map((_, i) => ({
      id: i,
      left: Math.random() * 100,
      top: Math.random() * 100,
      delay: Math.random() * 20,
      duration: 15 + Math.random() * 10,
      size: 1 + Math.random() * 2, // Variable sizes
      opacity: 0.3 + Math.random() * 0.4
    }));
  }, [particleCount]);

  return (
    <div className="dark-veil-container" aria-hidden="true">
      {/* Base gradient layer */}
      <div 
        className="dark-veil-gradient" 
        style={{ opacity }} 
      />
      
      {/* Animated particles (conditionally rendered) */}
      {enableAnimation && (
        <div className="dark-veil-particles">
          {particles.map((particle) => (
            <div
              key={particle.id}
              className="particle"
              style={{
                left: `${particle.left}%`,
                top: `${particle.top}%`,
                animationDelay: `${particle.delay}s`,
                animationDuration: `${particle.duration}s`,
                width: `${particle.size}px`,
                height: `${particle.size}px`,
                opacity: particle.opacity
              }}
            />
          ))}
        </div>
      )}
      
      {/* Optional mesh overlay */}
      {showMesh && (
        <div className="dark-veil-overlay" />
      )}
      
      {/* Radial glow spots */}
      <div className="dark-veil-glow dark-veil-glow-1" />
      <div className="dark-veil-glow dark-veil-glow-2" />
    </div>
  );
}

// Performance-optimized version for mobile
export function DarkVeilMobile() {
  return (
    <DarkVeil 
      opacity={0.25}
      particleCount={15}
      enableAnimation={false}
      showMesh={false}
    />
  );
}

// Minimal static version (no particles)
export function DarkVeilStatic() {
  return (
    <div className="dark-veil-container" aria-hidden="true">
      <div className="dark-veil-gradient" style={{ opacity: 0.3 }} />
      <div className="dark-veil-overlay" />
      <div className="dark-veil-glow dark-veil-glow-1" />
      <div className="dark-veil-glow dark-veil-glow-2" />
    </div>
  );
}