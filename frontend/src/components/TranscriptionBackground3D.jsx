import { useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Float, PerspectiveCamera, MeshDistortMaterial, Sparkles, Environment } from '@react-three/drei';

const AnimatedSphere = ({ position, scale, color, speed, distort }) => {
  return (
    <Float speed={2} rotationIntensity={1} floatIntensity={1}>
      <mesh position={position} scale={scale}>
        <sphereGeometry args={[1, 64, 64]} />
        <MeshDistortMaterial
          color={color}
          speed={speed}
          distort={distort}
          radius={1}
          roughness={0.1}
          metalness={0.5}
        />
      </mesh>
    </Float>
  );
};

const TranscriptionBackground3D = () => {
  return (
    <div className="fixed inset-0 z-0 pointer-events-none">
      <Canvas gl={{ alpha: true, antialias: true }} dpr={[1, 2]}>
        <PerspectiveCamera makeDefault position={[0, 0, 8]} />
        <ambientLight intensity={0.5} />
        <directionalLight position={[5, 5, 5]} intensity={1} />
        <pointLight position={[-5, -5, -5]} intensity={1} color="#e2e8f0" />

        {/* Main floating organic shapes */}
        <AnimatedSphere 
          position={[-4, 1, -2]} 
          scale={1.4} 
          color="#94a3b8" // Slate-400 (Silver)
          speed={1.5} 
          distort={0.4} 
        />
        <AnimatedSphere 
          position={[4, -1.5, -3]} 
          scale={1.8} 
          color="#334155" // Slate-700 (Dark Silver)
          speed={1.2} 
          distort={0.3} 
        />
        <AnimatedSphere 
          position={[0, 3.5, -5]} 
          scale={1.2} 
          color="#e2e8f0" // Slate-200 (Light Silver)
          speed={2} 
          distort={0.5} 
        />
        
        {/* Extra small accent spheres */}
        <AnimatedSphere 
          position={[2, 2, -1]} 
          scale={0.4} 
          color="#f8fafc" // Slate-50 (White Silver)
          speed={3} 
          distort={0.6} 
        />
        <AnimatedSphere 
          position={[-2, -3, -2]} 
          scale={0.6} 
          color="#64748b" // Slate-500 (Medium Silver)
          speed={2.5} 
          distort={0.4} 
        />

        {/* Background particles */}
        <Sparkles 
          count={80} 
          scale={12} 
          size={3} 
          speed={0.4} 
          opacity={0.6} 
          color="#ffffff"
        />
        
        <Environment preset="city" />
      </Canvas>
    </div>
  );
};

export default TranscriptionBackground3D;
