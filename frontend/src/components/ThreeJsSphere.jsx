import { useEffect, useRef } from 'react';
import * as THREE from 'three';

const ThreeJsSphere = () => {
  const containerRef = useRef(null);
  const cleanupRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const container = containerRef.current;

    // Configuration
    const CONFIG = {
      count: 6000,
      radius: 30,
      blockSize: 0.85,
      waveSpeed: 2.5,
      waveHeight: 14.0,
      colors: {
        background: 0xFFF5E6,
        gold: new THREE.Color(0xF59E0B),
        grey: new THREE.Color(0x94A3B8),
        blue: new THREE.Color(0x60A5FA)
      }
    };

    // Scene Setup
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(CONFIG.colors.background);
    scene.fog = new THREE.FogExp2(CONFIG.colors.background, 0.015);

    const camera = new THREE.PerspectiveCamera(
      60,
      container.clientWidth / container.clientHeight,
      0.1,
      1000
    );
    camera.position.z = 90;

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.setPixelRatio(window.devicePixelRatio);
    container.appendChild(renderer.domElement);

    // Lighting - Increased intensity for brighter appearance
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    scene.add(ambientLight);

    const mainLight = new THREE.PointLight(0xFFD700, 2.5, 200);
    mainLight.position.set(50, 50, 50);
    scene.add(mainLight);

    const blueLight = new THREE.PointLight(0x00BFFF, 2.8, 200);
    blueLight.position.set(-50, -20, -50);
    scene.add(blueLight);

    const fillLight = new THREE.PointLight(0xffffff, 1.5, 180);
    fillLight.position.set(0, 50, -50);
    scene.add(fillLight);

    // Geometry
    const geometry = new THREE.BoxGeometry(CONFIG.blockSize, CONFIG.blockSize, CONFIG.blockSize);
    const material = new THREE.MeshStandardMaterial({
      color: 0xffffff,
      roughness: 0.3,
      metalness: 0.8,
      flatShading: false
    });

    const mesh = new THREE.InstancedMesh(geometry, material, CONFIG.count);
    scene.add(mesh);

    // Data Setup
    const dummy = new THREE.Object3D();
    const initialPositions = [];
    const baseColors = [];
    const offsets = [];

    // Fibonacci Sphere Distribution
    const phi = Math.PI * (3 - Math.sqrt(5));

    for (let i = 0; i < CONFIG.count; i++) {
      const y = 1 - (i / (CONFIG.count - 1)) * 2;
      const radiusAtY = Math.sqrt(1 - y * y);
      const theta = phi * i;

      const x = Math.cos(theta) * radiusAtY;
      const z = Math.sin(theta) * radiusAtY;

      const dir = new THREE.Vector3(x, y, z).normalize();
      initialPositions.push(dir);

      offsets.push(Math.random() * 100);

      // Color Distribution: 60% Grey, 25% Blue, 15% Gold
      const rand = Math.random();
      let color;

      if (rand > 0.85) {
        color = CONFIG.colors.gold;
      } else if (rand > 0.60) {
        color = CONFIG.colors.blue;
      } else {
        color = CONFIG.colors.grey;
      }

      baseColors.push(color);
      mesh.setColorAt(i, color);

      // Initial placement
      dummy.position.copy(dir).multiplyScalar(CONFIG.radius);
      dummy.lookAt(0, 0, 0);
      dummy.updateMatrix();
      mesh.setMatrixAt(i, dummy.matrix);
    }

    // Mouse Interaction
    let mouseX = 0;
    let mouseY = 0;

    const handleMouseMove = (event) => {
      const rect = container.getBoundingClientRect();
      const windowHalfX = rect.width / 2;
      const windowHalfY = rect.height / 2;
      mouseX = (event.clientX - rect.left - windowHalfX) * 0.0005;
      mouseY = (event.clientY - rect.top - windowHalfY) * 0.0005;
    };

    container.addEventListener('mousemove', handleMouseMove);

    // Animation Loop
    const clock = new THREE.Clock();
    let animationId;

    function animate() {
      animationId = requestAnimationFrame(animate);

      const time = clock.getElapsedTime();

      // Rotate the whole sphere
      mesh.rotation.y += 0.002;
      mesh.rotation.x += 0.001;

      // Mouse interaction (gentle tilt)
      mesh.rotation.x += (mouseY - mesh.rotation.x) * 0.05;
      mesh.rotation.y += (mouseX - mesh.rotation.y) * 0.05;

      // Update Blocks
      for (let i = 0; i < CONFIG.count; i++) {
        const dir = initialPositions[i];
        const offset = offsets[i];

        // Wave Calculation
        const wave =
          Math.sin(dir.x * 4 + time * CONFIG.waveSpeed) +
          Math.cos(dir.y * 3 + time * CONFIG.waveSpeed) +
          Math.sin(dir.z * 5 + offset * 0.1);

        const extension = (Math.sin(wave) + 1) * 0.5;
        const dist = CONFIG.radius + extension * CONFIG.waveHeight;

        // Update Position
        dummy.position.copy(dir).multiplyScalar(dist);
        dummy.lookAt(0, 0, 0);

        // Scale Effect: Blocks get longer as they extend out
        dummy.scale.set(1, 1, 1 + extension * 2);

        dummy.updateMatrix();
        mesh.setMatrixAt(i, dummy.matrix);
      }

      mesh.instanceMatrix.needsUpdate = true;
      renderer.render(scene, camera);
    }

    // Handle Resize
    const handleResize = () => {
      if (!container) return;
      camera.aspect = container.clientWidth / container.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(container.clientWidth, container.clientHeight);
    };

    window.addEventListener('resize', handleResize);

    animate();

    // Cleanup function
    cleanupRef.current = () => {
      cancelAnimationFrame(animationId);
      window.removeEventListener('resize', handleResize);
      container.removeEventListener('mousemove', handleMouseMove);
      
      if (container && renderer.domElement && container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
      
      geometry.dispose();
      material.dispose();
      renderer.dispose();
    };

    return () => {
      if (cleanupRef.current) {
        cleanupRef.current();
      }
    };
  }, []);

  return (
    <div
      ref={containerRef}
      style={{
        width: '100%',
        height: '100%',
        minHeight: '400px'
      }}
    />
  );
};

export default ThreeJsSphere;
