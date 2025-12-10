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
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.z = 5;
    camera.position.y = 0;

    // Renderer
    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    mountRef.current.appendChild(renderer.domElement);

    // Group to hold all objects
    const mainGroup = new THREE.Group();
    scene.add(mainGroup);

    // --- Configuration ---
    const DOT_COLOR = 0x1e293b; // Darker slate-900 for better visibility
    const DOT_SIZE = 0.025; // Slightly larger points

    // --- Helper: Create Point Cloud from Geometry ---
    const createPointCloud = (geometry, count = 1000, scale = 1, position = [0,0,0], rotation = [0,0,0]) => {
        const material = new THREE.PointsMaterial({
            color: DOT_COLOR,
            size: DOT_SIZE,
            transparent: true,
            opacity: 0.8, // Increased opacity
        });

        // Sample points from the surface
        const sampler = new THREE.Mesh(geometry, new THREE.MeshBasicMaterial());
        const pointsGeometry = new THREE.BufferGeometry();
        
        // Simple random sampling within bounds (approximation)
        // For better results, we'd use MeshSurfaceSampler, but let's stick to core Three.js
        // Actually, let's just use vertices if low poly, or generate random points on surface.
        
        const vertices = [];
        
        // Custom sampling logic based on geometry type
        if (geometry.type === 'BoxGeometry') {
            const { width, height, depth } = geometry.parameters;
            for (let i = 0; i < count; i++) {
                // Randomly pick a face
                const face = Math.floor(Math.random() * 6);
                let x, y, z;
                const u = Math.random() - 0.5;
                const v = Math.random() - 0.5;

                if (face === 0) { x = width/2; y = u * height; z = v * depth; } // Right
                else if (face === 1) { x = -width/2; y = u * height; z = v * depth; } // Left
                else if (face === 2) { y = height/2; x = u * width; z = v * depth; } // Top
                else if (face === 3) { y = -height/2; x = u * width; z = v * depth; } // Bottom
                else if (face === 4) { z = depth/2; x = u * width; y = v * height; } // Front
                else if (face === 5) { z = -depth/2; x = u * width; y = v * height; } // Back
                
                vertices.push(x, y, z);
            }
        } else if (geometry.type === 'CylinderGeometry') {
            const { radiusTop, radiusBottom, height } = geometry.parameters;
            for (let i = 0; i < count; i++) {
                const theta = Math.random() * Math.PI * 2;
                const h = (Math.random() - 0.5) * height;
                // Interpolate radius
                const t = (h + height/2) / height;
                const r = radiusBottom * (1-t) + radiusTop * t;
                
                const x = r * Math.cos(theta);
                const z = r * Math.sin(theta);
                const y = h;
                vertices.push(x, y, z);
            }
        }

        pointsGeometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
        const points = new THREE.Points(pointsGeometry, material);
        
        points.scale.set(scale, scale, scale);
        points.position.set(...position);
        points.rotation.set(...rotation);
        
        return points;
    };

    // --- Create Objects ---

    // 1. Pillars (Background) - Museum Style
    // Base
    const baseGeo = new THREE.BoxGeometry(1.2, 0.4, 1.2);
    const base1 = createPointCloud(baseGeo, 800, 1, [-4, -2.5, -2]);
    const base2 = createPointCloud(baseGeo, 800, 1, [4, -2.5, -2]);
    mainGroup.add(base1);
    mainGroup.add(base2);

    // Shaft (Cylinder)
    const pillarGeo = new THREE.CylinderGeometry(0.5, 0.5, 5, 32); 
    const pillar1 = createPointCloud(pillarGeo, 3000, 1, [-4, 0, -2]);
    const pillar2 = createPointCloud(pillarGeo, 3000, 1, [4, 0, -2]);
    mainGroup.add(pillar1);
    mainGroup.add(pillar2);

    // Capital (Top)
    const capGeo = new THREE.BoxGeometry(1.1, 0.3, 1.1);
    const cap1 = createPointCloud(capGeo, 600, 1, [-4, 2.5, -2]);
    const cap2 = createPointCloud(capGeo, 600, 1, [4, 2.5, -2]);
    mainGroup.add(cap1);
    mainGroup.add(cap2);

    // 2. Floating Books
    const bookGeo = new THREE.BoxGeometry(1.2, 1.6, 0.25); // Slightly larger books
    const books = [];
    
    // Book 1 (Center left)
    const book1 = createPointCloud(bookGeo, 1200, 1, [-1.5, 0.5, 0], [0.2, 0.4, 0]);
    books.push(book1);
    mainGroup.add(book1);

    // Book 2 (Center right)
    const book2 = createPointCloud(bookGeo, 1200, 1, [1.5, -0.5, 0.5], [-0.2, -0.3, 0.1]);
    books.push(book2);
    mainGroup.add(book2);

    // Book 3 (Background floating)
    const book3 = createPointCloud(bookGeo, 1200, 0.8, [0, 1.8, -1], [0.5, 0.5, 0]);
    books.push(book3);
    mainGroup.add(book3);
    
    // Book 4 (New - Bottom Center)
    const book4 = createPointCloud(bookGeo, 1200, 0.9, [0, -1.5, 1], [0.1, 0, -0.2]);
    books.push(book4);
    mainGroup.add(book4);


    // --- Animation Loop ---
    let frameId;
    const animate = () => {
        frameId = requestAnimationFrame(animate);

        // Rotate pillars slowly
        pillar1.rotation.y += 0.002;
        pillar2.rotation.y += 0.002;

        // Float and rotate books
        const time = Date.now() * 0.001;

        books.forEach((book, i) => {
            book.rotation.x += 0.003 * (i % 2 === 0 ? 1 : -1);
            book.rotation.y += 0.005 * (i % 2 === 0 ? 1 : -1);
            
            // Floating motion
            book.position.y += Math.sin(time + i) * 0.002;
        });

        // Mouse interaction (parallax)
        // (Simplified: just constant gentle movement for now)
        mainGroup.rotation.y = Math.sin(time * 0.2) * 0.05;

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

    // Cleanup
    return () => {
        window.removeEventListener('resize', handleResize);
        cancelAnimationFrame(frameId);
        if (mountRef.current) {
            mountRef.current.removeChild(renderer.domElement);
        }
        // Dispose geometries/materials
        pillarGeo.dispose();
        bookGeo.dispose();
        scene.traverse((object) => {
            if (object.geometry) object.geometry.dispose();
            if (object.material) object.material.dispose();
        });
    };
  }, []);

  return (
    <div 
      ref={mountRef} 
      className="fixed inset-0 z-0 pointer-events-none"
      style={{ opacity: 0.6 }} // Subtle blend
    />
  );
};

export default LibraryBackground3D;
