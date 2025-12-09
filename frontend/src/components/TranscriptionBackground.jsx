import { useRef, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Float, Stars, Sparkles } from '@react-three/drei';
import * as THREE from 'three';

const FloatingParticle = ({ position, color, scale }) => {
  const mesh = useRef();
  
  useFrame((state) => {
    const t = state.clock.getElapsedTime();
    mesh.current.rotation.x = Math.cos(t / 4) / 2;
    mesh.current.rotation.y = Math.sin(t / 4) / 2;
    mesh.current.rotation.z = Math.sin(t / 1.5) / 2;
    mesh.current.position.y = position[1] + Math.sin(t / 1.5) / 10;
  });

  return (
    <Float speed={1.5} rotationIntensity={1} floatIntensity={2}>
      <mesh ref={mesh} position={position} scale={scale}>
        <dodecahedronGeometry args={[1, 0]} />
        <meshStandardMaterial 
          color={color} 
          roughness={0.1} 
          metalness={0.8} 
          emissive={color}
          emissiveIntensity={0.2}
        />
      </mesh>
    </Float>
  );
};

const Scene = () => {
  const particles = useMemo(() => {
    return Array.from({ length: 15 }).map((_, i) => ({
      position: [
        (Math.random() - 0.5) * 15,
        (Math.random() - 0.5) * 10,
        (Math.random() - 0.5) * 10
      ],
      scale: Math.random() * 0.4 + 0.1,
      color: Math.random() > 0.5 ? '#d97706' : '#475569' // Amber-600 or Slate-600 (Darker for visibility on light bg)
    }));
  }, []);

  return (
    <>
      <ambientLight intensity={0.8} />
      <pointLight position={[10, 10, 10]} intensity={1} color="#fbbf24" />
      <pointLight position={[-10, -10, -10]} intensity={0.5} color="#3b82f6" />
      
      {/* Darker stars/sparkles for light background */}
      <Stars radius={100} depth={50} count={2000} factor={4} saturation={0} fade speed={1} /> 
      <Sparkles count={80} scale={12} size={3} speed={0.4} opacity={0.6} color="#b45309" />
      
      {particles.map((props, i) => (
        <FloatingParticle key={i} {...props} />
      ))}
    </>
  );
};

const TranscriptionBackground = () => {
  return (
    <div className="fixed inset-0 z-0 bg-[#F5EACE]">
      {/* Light Golden Gradient similar to Home */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_left,_var(--tw-gradient-stops))] from-[#F5EACE] via-[#E5DDB8] to-[#cbd5e1] opacity-100" />
      
      <Canvas camera={{ position: [0, 0, 8], fov: 45 }}>
        <Scene />
      </Canvas>
      
      {/* Subtle overlay for depth */}
      <div className="absolute inset-0 bg-gradient-to-t from-slate-200/20 via-transparent to-white/10 pointer-events-none" />
    </div>
  );
};

export default TranscriptionBackground;
