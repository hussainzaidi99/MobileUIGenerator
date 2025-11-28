// frontend/src/components/DynamicBackgroundPreview.jsx
import React, { useEffect, useRef } from 'react';

export default function DynamicBackgroundPreview({ config, children }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    if (!config?.enabled || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    
    // Set canvas size
    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;

    // Render gradient
    if (config.gradient) {
      renderGradient(ctx, config.gradient, canvas.width, canvas.height);
    }

    // Render floating shapes
    if (config.floating_shapes?.enabled) {
      renderFloatingShapes(ctx, config.floating_shapes, canvas.width, canvas.height);
    }

    // Animation loop
    if (config.animations?.enabled) {
      let animationId;
      let frame = 0;

      const animate = () => {
        frame++;
        
        // Clear and redraw
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        if (config.gradient) {
          renderGradient(ctx, config.gradient, canvas.width, canvas.height);
        }
        
        if (config.floating_shapes?.enabled) {
          renderFloatingShapes(
            ctx, 
            config.floating_shapes, 
            canvas.width, 
            canvas.height,
            frame
          );
        }

        animationId = requestAnimationFrame(animate);
      };

      animate();

      return () => {
        if (animationId) cancelAnimationFrame(animationId);
      };
    }
  }, [config]);

  if (!config?.enabled) {
    return <div className="background-preview-disabled">{children}</div>;
  }

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%' }}>
      {/* Background Canvas */}
      <canvas
        ref={canvasRef}
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          zIndex: 0,
          pointerEvents: 'none',
        }}
      />
      
      {/* Content Layer */}
      <div style={{ position: 'relative', zIndex: 1 }}>
        {children}
      </div>
    </div>
  );
}

// ============================================================================
// RENDERING HELPERS
// ============================================================================

function renderGradient(ctx, gradientConfig, width, height) {
  if (!gradientConfig || !gradientConfig.colors) return;

  let gradient;

  if (gradientConfig.type === 'linear') {
    const angle = (gradientConfig.angle || 135) * (Math.PI / 180);
    const x1 = width / 2 - Math.cos(angle) * width / 2;
    const y1 = height / 2 - Math.sin(angle) * height / 2;
    const x2 = width / 2 + Math.cos(angle) * width / 2;
    const y2 = height / 2 + Math.sin(angle) * height / 2;
    
    gradient = ctx.createLinearGradient(x1, y1, x2, y2);
  } else if (gradientConfig.type === 'radial') {
    gradient = ctx.createRadialGradient(
      width / 2, 
      height / 2, 
      0, 
      width / 2, 
      height / 2, 
      Math.max(width, height) / 2
    );
  }

  // Add color stops
  gradientConfig.colors.forEach((color, index) => {
    gradient.addColorStop(index / (gradientConfig.colors.length - 1), color);
  });

  ctx.globalAlpha = gradientConfig.opacity || 0.08;
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, width, height);
  ctx.globalAlpha = 1;
}

function renderFloatingShapes(ctx, shapesConfig, width, height, frame = 0) {
  if (!shapesConfig.shapes) return;

  shapesConfig.shapes.forEach((shape, index) => {
    const x = (shape.position.x / 100) * width;
    const y = (shape.position.y / 100) * height;
    
    // Animate position
    const animOffset = Math.sin((frame + index * 100) * 0.01) * 30;
    const finalY = y + animOffset;

    ctx.save();
    ctx.globalAlpha = shape.opacity || 0.03;
    ctx.filter = `blur(${shape.blur || 40}px)`;
    ctx.fillStyle = 'rgba(255, 255, 255, 0.5)';

    // Render shape based on type
    switch (shape.type) {
      case 'circle':
        ctx.beginPath();
        ctx.arc(x, finalY, shape.size / 2, 0, Math.PI * 2);
        ctx.fill();
        break;

      case 'square':
        ctx.fillRect(x - shape.size / 2, finalY - shape.size / 2, shape.size, shape.size);
        break;

      case 'blob':
        // Organic blob shape
        renderBlob(ctx, x, finalY, shape.size);
        break;

      case 'triangle':
        ctx.beginPath();
        ctx.moveTo(x, finalY - shape.size / 2);
        ctx.lineTo(x + shape.size / 2, finalY + shape.size / 2);
        ctx.lineTo(x - shape.size / 2, finalY + shape.size / 2);
        ctx.closePath();
        ctx.fill();
        break;
    }

    ctx.restore();
  });
}

function renderBlob(ctx, x, y, size) {
  // Organic blob using bezier curves
  ctx.beginPath();
  ctx.moveTo(x, y - size / 2);
  
  // Top curve
  ctx.bezierCurveTo(
    x + size / 3, y - size / 2,
    x + size / 2, y - size / 3,
    x + size / 2, y
  );
  
  // Right curve
  ctx.bezierCurveTo(
    x + size / 2, y + size / 3,
    x + size / 3, y + size / 2,
    x, y + size / 2
  );
  
  // Bottom curve
  ctx.bezierCurveTo(
    x - size / 3, y + size / 2,
    x - size / 2, y + size / 3,
    x - size / 2, y
  );
  
  // Left curve
  ctx.bezierCurveTo(
    x - size / 2, y - size / 3,
    x - size / 3, y - size / 2,
    x, y - size / 2
  );
  
  ctx.fill();
}