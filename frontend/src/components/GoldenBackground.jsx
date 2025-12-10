import DigitalGlobe from './DigitalGlobe';
import LibraryBackground3D from './LibraryBackground3D';
import TranscriptionBackground3D from './TranscriptionBackground3D';

const GoldenBackground = ({ variant = 'home' }) => {
  return (
    <>
      {/* Background - Lighter Cream to Dark Grayish Transition with Light Beam */}
      <div className="fixed inset-0 z-[-1]" style={{
        background: `radial-gradient(ellipse 200% 150% at 0% 100%, #F5EACE 0%, #F3E8C4 10%, #F0E5BA 18%, #EDE2B0 26%, #E5DDB8 35%, #cbd5e1 50%, #94a3b8 65%, #64748b 78%, #475569 90%, #1e293b 100%)`
      }}>
        {/* Subtle Noise Texture */}
        <div className="absolute inset-0 opacity-[0.04]" style={{ 
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E")` 
        }}></div>
        
        {/* Straight Light Beam - Diagonal from Top-Left to Bottom-Right */}
        <div 
          className="absolute pointer-events-none z-[1]" 
          style={{
            top: 0,
            left: 0,
            width: '800px',
            height: '800px',
            background: 'linear-gradient(to right, rgba(255, 255, 255, 0.5) 0%, rgba(245, 234, 206, 0.35) 30%, rgba(243, 232, 196, 0.2) 60%, transparent 100%)',
            transform: 'rotate(45deg)',
            transformOrigin: 'top left',
            mixBlendMode: 'overlay'
          }}
        />
        
        {/* Soft Glow Layer */}
        <div 
          className="absolute pointer-events-none z-[0]" 
          style={{
            top: 0,
            left: 0,
            width: '900px',
            height: '900px',
            background: 'linear-gradient(to right, rgba(255, 255, 255, 0.25) 0%, rgba(245, 234, 206, 0.12) 40%, transparent 80%)',
            transform: 'rotate(45deg)',
            transformOrigin: 'top left',
            mixBlendMode: 'soft-light',
            filter: 'blur(30px)'
          }}
        />
      </div>

      {variant === 'home' ? <DigitalGlobe /> : variant === 'library' ? <LibraryBackground3D /> : <TranscriptionBackground3D />}
    </>
  );
};

export default GoldenBackground;
