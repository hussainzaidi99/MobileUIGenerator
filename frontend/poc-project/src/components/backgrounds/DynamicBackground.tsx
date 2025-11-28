// src/components/backgrounds/DynamicBackground.tsx
/**
 * Dynamic Background Component for React Native
 * Renders context-aware backgrounds with animations
 * Zero impact on existing component logic
 * 
 * @version 1.0.0
 * @production-ready
 */

import React, { useEffect, useRef } from 'react';
import { View, StyleSheet, Dimensions, Animated } from 'react-native';
import LinearGradient from 'react-native-linear-gradient';

const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get('window');

// ============================================================================
// TYPE DEFINITIONS
// ============================================================================

interface BackgroundConfig {
  enabled: boolean;
  primary_style: 'gradient' | 'geometric' | 'floating_shapes' | 'glassmorphism' | 'mesh_gradient' | 'aurora';
  secondary_style: string;
  gradient: {
    type: 'linear' | 'radial';
    colors: string[];
    angle?: number;
    opacity: number;
  };
  floating_shapes: {
    enabled: boolean;
    shapes: Array<{
      type: 'circle' | 'square' | 'blob' | 'triangle';
      size: number;
      position: { x: number; y: number };
      opacity: number;
      blur: number;
      rotation: number;
      animation: {
        type: 'float' | 'rotate' | 'pulse';
        duration: number;
        direction: 'alternate' | 'normal';
      };
    }>;
  };
  animations: {
    enabled: boolean;
    duration: number;
  };
}

interface Props {
  config: BackgroundConfig;
  children: React.ReactNode;
}

interface GradientConfig {
  type: 'linear' | 'radial';
  colors: string[];
  angle?: number;
  opacity: number;
}

interface ShapeConfig {
  type: 'circle' | 'square' | 'blob' | 'triangle';
  size: number;
  position: { x: number; y: number };
  opacity: number;
  blur: number;
  rotation: number;
  animation: {
    type: 'float' | 'rotate' | 'pulse';
    duration: number;
    direction: 'alternate' | 'normal';
  };
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

const DynamicBackground: React.FC<Props> = ({ config, children }) => {
  // Early return if background is disabled
  if (!config?.enabled) {
    return <>{children}</>;
  }

  return (
    <View style={styles.container}>
      {/* Layer 1: Base Gradient */}
      {config.gradient && <GradientLayer config={config.gradient} />}
      
      {/* Layer 2: Floating Shapes */}
      {config.floating_shapes?.enabled && config.floating_shapes.shapes && (
        <FloatingShapesLayer 
          shapes={config.floating_shapes.shapes}
          animationsEnabled={config.animations?.enabled ?? true}
        />
      )}
      
      {/* Layer 3: Content (your UI components) */}
      <View style={styles.content}>
        {children}
      </View>
    </View>
  );
};

// ============================================================================
// GRADIENT LAYER
// ============================================================================

const GradientLayer: React.FC<{ config: GradientConfig }> = ({ config }) => {
  // Validate colors array
  if (!config.colors || config.colors.length < 2) {
    console.warn('[DynamicBackground] Gradient requires at least 2 colors');
    return null;
  }

  if (config.type === 'linear') {
    const angle = config.angle ?? 135;
    
    // Convert angle to start/end points
    const angleRad = (angle - 90) * (Math.PI / 180);
    const startX = 0.5 - Math.cos(angleRad) / 2;
    const startY = 0.5 - Math.sin(angleRad) / 2;
    const endX = 0.5 + Math.cos(angleRad) / 2;
    const endY = 0.5 + Math.sin(angleRad) / 2;
    
    return (
      <LinearGradient
        colors={config.colors}
        start={{ x: startX, y: startY }}
        end={{ x: endX, y: endY }}
        style={[
          styles.gradientLayer,
          { opacity: config.opacity ?? 0.08 }
        ]}
      />
    );
  }
  
  // Radial gradient (approximated with center-to-corner)
  return (
    <LinearGradient
      colors={config.colors}
      start={{ x: 0.5, y: 0.5 }}
      end={{ x: 1, y: 1 }}
      style={[
        styles.gradientLayer,
        { opacity: config.opacity ?? 0.08 }
      ]}
    />
  );
};

// ============================================================================
// FLOATING SHAPES LAYER
// ============================================================================

const FloatingShapesLayer: React.FC<{ 
  shapes: ShapeConfig[]; 
  animationsEnabled: boolean;
}> = ({ shapes, animationsEnabled }) => {
  return (
    <View style={styles.shapesLayer} pointerEvents="none">
      {shapes.map((shape, index) => (
        <FloatingShape
          key={`shape-${index}`}
          shape={shape}
          animationsEnabled={animationsEnabled}
        />
      ))}
    </View>
  );
};

// ============================================================================
// INDIVIDUAL FLOATING SHAPE
// ============================================================================

const FloatingShape: React.FC<{ 
  shape: ShapeConfig; 
  animationsEnabled: boolean;
}> = ({ shape, animationsEnabled }) => {
  const translateY = useRef(new Animated.Value(0)).current;
  const translateX = useRef(new Animated.Value(0)).current;
  const rotate = useRef(new Animated.Value(0)).current;
  const scale = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    if (!animationsEnabled) return;

    const duration = shape.animation?.duration ?? 4000;

    // Floating animation (up/down)
    const floatAnimation = Animated.loop(
      Animated.sequence([
        Animated.timing(translateY, {
          toValue: -30,
          duration: duration / 2,
          useNativeDriver: true,
        }),
        Animated.timing(translateY, {
          toValue: 0,
          duration: duration / 2,
          useNativeDriver: true,
        }),
      ])
    );

    // Horizontal drift
    const driftAnimation = Animated.loop(
      Animated.sequence([
        Animated.timing(translateX, {
          toValue: 20,
          duration: duration,
          useNativeDriver: true,
        }),
        Animated.timing(translateX, {
          toValue: 0,
          duration: duration,
          useNativeDriver: true,
        }),
      ])
    );

    // Rotation animation
    const rotateAnimation = Animated.loop(
      Animated.timing(rotate, {
        toValue: 1,
        duration: duration * 2,
        useNativeDriver: true,
      })
    );

    // Pulse animation
    const pulseAnimation = Animated.loop(
      Animated.sequence([
        Animated.timing(scale, {
          toValue: 1.1,
          duration: duration / 3,
          useNativeDriver: true,
        }),
        Animated.timing(scale, {
          toValue: 1,
          duration: duration / 3,
          useNativeDriver: true,
        }),
      ])
    );

    // Start all animations
    floatAnimation.start();
    driftAnimation.start();
    rotateAnimation.start();
    pulseAnimation.start();

    // Cleanup
    return () => {
      floatAnimation.stop();
      driftAnimation.stop();
      rotateAnimation.stop();
      pulseAnimation.stop();
    };
  }, [animationsEnabled, shape.animation?.duration, translateY, translateX, rotate, scale]);

  const rotateInterpolate = rotate.interpolate({
    inputRange: [0, 1],
    outputRange: ['0deg', '360deg'],
  });

  const shapeStyle = {
    position: 'absolute' as const,
    left: `${shape.position.x}%`,
    top: `${shape.position.y}%`,
    width: shape.size,
    height: shape.size,
    opacity: shape.opacity ?? 0.03,
    transform: [
      { translateY },
      { translateX },
      { rotate: rotateInterpolate },
      { scale },
    ],
  };

  // Shape-specific rendering
  const renderShape = () => {
    const baseStyle = {
      width: '100%',
      height: '100%',
      backgroundColor: 'rgba(255, 255, 255, 0.5)',
    };

    switch (shape.type) {
      case 'circle':
        return (
          <View 
            style={[
              baseStyle, 
              { borderRadius: shape.size / 2 }
            ]} 
          />
        );
      
      case 'square':
        return (
          <View 
            style={[
              baseStyle, 
              { borderRadius: 8 }
            ]} 
          />
        );
      
      case 'blob':
        // Organic blob shape (using asymmetric border radius)
        return (
          <View 
            style={[
              baseStyle,
              { 
                borderTopLeftRadius: shape.size * 0.6,
                borderTopRightRadius: shape.size * 0.4,
                borderBottomLeftRadius: shape.size * 0.4,
                borderBottomRightRadius: shape.size * 0.6,
              }
            ]} 
          />
        );
      
      case 'triangle':
        // Triangle using border trick
        return (
          <View 
            style={{
              width: 0,
              height: 0,
              borderLeftWidth: shape.size / 2,
              borderRightWidth: shape.size / 2,
              borderBottomWidth: shape.size,
              borderLeftColor: 'transparent',
              borderRightColor: 'transparent',
              borderBottomColor: 'rgba(255, 255, 255, 0.5)',
            }} 
          />
        );
      
      default:
        return <View style={baseStyle} />;
    }
  };

  return (
    <Animated.View style={shapeStyle}>
      {renderShape()}
    </Animated.View>
  );
};

// ============================================================================
// STYLES
// ============================================================================

const styles = StyleSheet.create({
  container: {
    flex: 1,
    position: 'relative',
  },
  gradientLayer: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    zIndex: 0,
  },
  shapesLayer: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    zIndex: 1,
    overflow: 'hidden',
  },
  content: {
    flex: 1,
    zIndex: 2,
  },
});

export default DynamicBackground;

// ============================================================================
// USAGE EXAMPLE
// ============================================================================
/*
import DynamicBackground from './components/backgrounds/DynamicBackground';

export default function LoginScreen({ backgroundConfig }) {
  return (
    <DynamicBackground config={backgroundConfig}>
      <SafeAreaView style={styles.container}>
        <ScrollView>
          {/* Your existing UI components *\/}
        </ScrollView>
      </SafeAreaView>
    </DynamicBackground>
  );
}
*/