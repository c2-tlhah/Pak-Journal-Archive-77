import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';

/**
 * 3D Tech Globe Component
 * FIXED: Shape (Aspect Ratio) & Continent Mapping (Land vs Ocean)
 */
const DigitalGlobe = () => {
  const mountRef = useRef(null);

  useEffect(() => {
    if (!mountRef.current) return;

    // --- Scene Setup ---
    const scene = new THREE.Scene();
    
    // Get exact container dimensions to prevent "egg" distortion
    const { clientWidth: width, clientHeight: height } = mountRef.current;

    // Camera
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.z = 3.2; 
    
    if (width > 768) {
        camera.position.x = -1.0; 
    }

    // Renderer
    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2)); 
    mountRef.current.appendChild(renderer.domElement);

    // Groups
    const globeGroup = new THREE.Group(); 
    scene.add(globeGroup);
    
    // Tilt
    globeGroup.rotation.z = 0.2;
    globeGroup.rotation.x = 0.3;

    // --- Configuration ---
    const GLOBE_RADIUS = 0.75; 
    // Lighter cream color matching theme (#F5EACE)
    const DOT_COLOR = 0xF5EACE; 
    const DOT_SIZE = 0.022; 
    const DENSITY_STEP = 5; 

    // --- Placeholder ---
    const placeholderGeo = new THREE.IcosahedronGeometry(GLOBE_RADIUS, 2);
    const placeholderMat = new THREE.MeshBasicMaterial({ 
        color: DOT_COLOR, 
        wireframe: true, 
        transparent: true, 
        opacity: 0.1
    });
    const placeholderMesh = new THREE.Mesh(placeholderGeo, placeholderMat);
    globeGroup.add(placeholderMesh);

    // --- Load Earth Map ---
    const textureLoader = new THREE.TextureLoader();
    // Using specular map: Bright = Water, Dark = Land
    const earthImageUrl = 'https://raw.githubusercontent.com/mrdoob/three.js/master/examples/textures/planets/earth_specular_2048.jpg';

    const image = new Image();
    image.crossOrigin = "Anonymous";
    image.onload = () => {
        if (mountRef.current) { // Check if still mounted
            globeGroup.remove(placeholderMesh);
            placeholderGeo.dispose();
            placeholderMat.dispose();

            // 1. Scan image
            const canvas = document.createElement('canvas');
            canvas.width = image.width;
            canvas.height = image.height;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(image, 0, 0);
            const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
            const data = imageData.data;

            const continentPoints = [];
            
            // 2. Generate points
            for (let y = 0; y < canvas.height; y += DENSITY_STEP) {
                for (let x = 0; x < canvas.width; x += DENSITY_STEP) {
                    const i = (y * canvas.width + x) * 4;
                    const brightness = data[i];

                    // FIXED LOGIC: Low brightness = Land
                    if (brightness < 80) { 
                        const lat = (Math.PI / 2) - (y / canvas.height) * Math.PI;
                        const lon = (x / canvas.width) * 2 * Math.PI - Math.PI;
                        
                        const r = GLOBE_RADIUS;
                        const posX = r * Math.cos(lat) * Math.cos(lon);
                        const posY = r * Math.sin(lat);
                        const posZ = r * Math.cos(lat) * Math.sin(lon);

                        continentPoints.push(posX, posY, posZ);
                    }
                }
            }

            // 3. Create Particles
            if (continentPoints.length > 0) {
                const particlesGeometry = new THREE.BufferGeometry();
                const particlesPos = new Float32Array(continentPoints);
                particlesGeometry.setAttribute('position', new THREE.BufferAttribute(particlesPos, 3));
                
                const particlesMaterial = new THREE.PointsMaterial({
                    size: DOT_SIZE,
                    color: DOT_COLOR,
                    transparent: true,
                    opacity: 0.95, 
                    blending: THREE.AdditiveBlending,
                    sizeAttenuation: true,
                    depthWrite: false
                });
                
                const particlesMesh = new THREE.Points(particlesGeometry, particlesMaterial);
                particlesMesh.rotation.y = -Math.PI / 2; 
                globeGroup.add(particlesMesh);

                // Add prominent earth outline (wireframe sphere)
                const outlineGeo = new THREE.SphereGeometry(GLOBE_RADIUS, 64, 64);
                const outlineMat = new THREE.MeshBasicMaterial({
                    color: 0xF5EACE,
                    wireframe: true,
                    transparent: true,
                    opacity: 0.15,
                    blending: THREE.AdditiveBlending
                });
                const outlineMesh = new THREE.Mesh(outlineGeo, outlineMat);
                globeGroup.add(outlineMesh);

                // 4. Create connections
                const geometryVertices = [];
                const maxDistance = 0.1; 
                const subsetSize = 2000; 
                
                const indices = [];
                for(let i=0; i<subsetSize; i++) {
                    indices.push(Math.floor(Math.random() * (continentPoints.length / 3)) * 3);
                }

                for (let i = 0; i < indices.length; i++) {
                    const idxA = indices[i];
                    const x1 = continentPoints[idxA];
                    const y1 = continentPoints[idxA+1];
                    const z1 = continentPoints[idxA+2];
                    const v1 = new THREE.Vector3(x1, y1, z1);

                    let connections = 0;
                    for (let j = i + 1; j < indices.length; j++) {
                        if (connections > 2) break; 

                        const idxB = indices[j];
                        const x2 = continentPoints[idxB];
                        const y2 = continentPoints[idxB+1];
                        const z2 = continentPoints[idxB+2];
                        const v2 = new THREE.Vector3(x2, y2, z2);

                        if (v1.distanceTo(v2) < maxDistance) {
                            geometryVertices.push(x1, y1, z1);
                            geometryVertices.push(x2, y2, z2);
                            connections++;
                        }
                    }
                }

                if (geometryVertices.length > 0) {
                    const lineGeometry = new THREE.BufferGeometry();
                    lineGeometry.setAttribute('position', new THREE.Float32BufferAttribute(geometryVertices, 3));
                    const lineMaterial = new THREE.LineBasicMaterial({
                        color: DOT_COLOR,
                        transparent: true,
                        opacity: 0.2, 
                        blending: THREE.NormalBlending
                    });
                    const lineMesh = new THREE.LineSegments(lineGeometry, lineMaterial);
                    lineMesh.rotation.y = -Math.PI / 2;
                    globeGroup.add(lineMesh);
                }
            }
        }
    };
    image.src = earthImageUrl;

    // --- INTERACTION ---
    let isDragging = false;
    let previousMousePosition = { x: 0, y: 0 };
    let velX = 0;
    let velY = 0.001; 

    const onMouseDown = (e) => {
        isDragging = true;
        previousMousePosition = { x: e.clientX, y: e.clientY };
        velX = 0;
        velY = 0;
    };

    const onMouseMove = (e) => {
        if (isDragging) {
            const deltaMove = {
                x: e.clientX - previousMousePosition.x,
                y: e.clientY - previousMousePosition.y
            };
            const rotateSpeed = 0.004;
            globeGroup.rotation.y += deltaMove.x * rotateSpeed;
            globeGroup.rotation.x += deltaMove.y * rotateSpeed;
            velY = deltaMove.x * rotateSpeed * 0.1; 
            velX = deltaMove.y * rotateSpeed * 0.1;
            previousMousePosition = { x: e.clientX, y: e.clientY };
        }
    };

    const onMouseUp = () => {
        isDragging = false;
    };

    window.addEventListener('mousedown', onMouseDown);
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
    window.addEventListener('touchstart', (e) => onMouseDown(e.touches[0]));
    window.addEventListener('touchmove', (e) => onMouseMove(e.touches[0]));
    window.addEventListener('touchend', onMouseUp);

    // Animation Loop
    let frameId;
    let time = 0;
    const animate = () => {
        time += 0.01;
        
        // Pulsing shine effect for dots
        globeGroup.children.forEach(child => {
            if (child instanceof THREE.Points) {
                const pulse = 0.85 + Math.sin(time * 2) * 0.15;
                child.material.opacity = pulse;
            }
        });
        
        if (!isDragging) {
            globeGroup.rotation.y += velY;
            globeGroup.rotation.x += velX;
            velY *= 0.96;
            velX *= 0.96;
            if (Math.abs(velY) < 0.001) {
                 if (velY < 0.001) velY += 0.00005;
            }
        }
        renderer.render(scene, camera);
        frameId = requestAnimationFrame(animate);
    };
    animate();

    const handleResize = () => {
        if (!mountRef.current) return;
        const newWidth = mountRef.current.clientWidth;
        const newHeight = mountRef.current.clientHeight;
        
        camera.aspect = newWidth / newHeight;
        
        if (newWidth > 768) {
            camera.position.x = -1.0; 
        } else {
            camera.position.x = 0; 
        }
        
        camera.updateProjectionMatrix();
        renderer.setSize(newWidth, newHeight);
    };

    window.addEventListener('resize', handleResize);
    handleResize();

    return () => {
        window.removeEventListener('mousedown', onMouseDown);
        window.removeEventListener('mousemove', onMouseMove);
        window.removeEventListener('mouseup', onMouseUp);
        window.removeEventListener('touchstart', onMouseDown);
        window.removeEventListener('touchmove', onMouseMove);
        window.removeEventListener('touchend', onMouseUp);
        window.removeEventListener('resize', handleResize);
        cancelAnimationFrame(frameId);
        if (mountRef.current && mountRef.current.contains(renderer.domElement)) {
            mountRef.current.removeChild(renderer.domElement);
        }
        renderer.dispose();
    };
  }, []);

  return (
    <div 
        ref={mountRef} 
        className="fixed top-0 left-0 w-full h-full cursor-grab active:cursor-grabbing z-0"
        style={{ opacity: 1 }} 
    />
  );
};

export default DigitalGlobe;
