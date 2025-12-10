import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';

const LibraryBackground3D = () => {
  const mountRef = useRef(null);

  useEffect(() => {
    if (!mountRef.current) return;

    // --- Scene Setup ---
    const scene = new THREE.Scene();
    const { clientWidth: width, clientHeight: height } = mountRef.current;

    // Camera
    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 100);
    camera.position.z = 25;

    // Renderer
    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    mountRef.current.appendChild(renderer.domElement);

    // --- Objects ---
    const group = new THREE.Group();
    scene.add(group);

    // Geometries for "Knowledge Blocks"
    const geometries = [
      new THREE.IcosahedronGeometry(1, 0), // Complex
      new THREE.OctahedronGeometry(1, 0),  // Medium
      new THREE.BoxGeometry(1.2, 1.2, 1.2), // Structured
    ];

    // Materials
    const material = new THREE.MeshBasicMaterial({ 
      color: 0x475569, // Slate 600 - Lighter than before
      wireframe: true,
      transparent: true,
      opacity: 0.15
    });
    
    const accentMaterial = new THREE.MeshBasicMaterial({ 
      color: 0xd97706, // Amber 600
      wireframe: true,
      transparent: true,
      opacity: 0.3
    });

    const shapes = [];
    const count = 45; // Number of floating objects

    for (let i = 0; i < count; i++) {
      const geom = geometries[Math.floor(Math.random() * geometries.length)];
      const isAccent = Math.random() > 0.85; // 15% chance of accent color
      const mesh = new THREE.Mesh(geom, isAccent ? accentMaterial : material);
      
      // Random position spread
      mesh.position.x = (Math.random() - 0.5) * 50;
      mesh.position.y = (Math.random() - 0.5) * 40;
      mesh.position.z = (Math.random() - 0.5) * 25;
      
      // Random rotation
      mesh.rotation.x = Math.random() * Math.PI;
      mesh.rotation.y = Math.random() * Math.PI;
      
      // Random scale
      const scale = Math.random() * 1.2 + 0.4;
      mesh.scale.set(scale, scale, scale);
      
      // Store animation data
      mesh.userData = {
        rotSpeedX: (Math.random() - 0.5) * 0.005,
        rotSpeedY: (Math.random() - 0.5) * 0.005,
        floatSpeed: Math.random() * 0.002 + 0.001,
        floatOffset: Math.random() * Math.PI * 2,
        initialY: mesh.position.y,
        initialX: mesh.position.x
      };
      
      group.add(mesh);
      shapes.push(mesh);
    }

    // --- Animation Loop ---
    let frameId;
    const animate = () => {
      frameId = requestAnimationFrame(animate);
      
      const time = Date.now() * 0.001;

      // Gentle global rotation
      group.rotation.y = Math.sin(time * 0.05) * 0.05;

      shapes.forEach(mesh => {
        // Rotate individual shapes
        mesh.rotation.x += mesh.userData.rotSpeedX;
        mesh.rotation.y += mesh.userData.rotSpeedY;
        
        // Float up and down (breathing effect)
        mesh.position.y = mesh.userData.initialY + Math.sin(time + mesh.userData.floatOffset) * 1.5;
        
        // Subtle horizontal drift
        mesh.position.x = mesh.userData.initialX + Math.cos(time * 0.5 + mesh.userData.floatOffset) * 0.5;
      });

      renderer.render(scene, camera);
    };

    animate();

    // --- Resize Handler ---
    const handleResize = () => {
        if (!mountRef.current) return;
        const width = mountRef.current.clientWidth;
        const height = mountRef.current.clientHeight;
        renderer.setSize(width, height);
        camera.aspect = width / height;
        camera.updateProjectionMatrix();
    };

    window.addEventListener('resize', handleResize);

    return () => {
        window.removeEventListener('resize', handleResize);
        cancelAnimationFrame(frameId);
        if (mountRef.current) {
            mountRef.current.removeChild(renderer.domElement);
        }
        geometries.forEach(g => g.dispose());
        material.dispose();
        accentMaterial.dispose();
    };
  }, []);

  return <div ref={mountRef} className="absolute inset-0 z-0 pointer-events-none" />;
};

export default LibraryBackground3D;