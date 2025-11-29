import { Navigate, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { motion } from 'framer-motion';
import { Lock, Radio, ShieldAlert, ArrowRight, Home } from 'lucide-react';

const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  const navigate = useNavigate();

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-amber-50 via-slate-100 to-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-slate-900 mx-auto mb-4"></div>
          <p className="text-slate-600 font-medium">Loading...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen w-full flex items-center justify-center relative overflow-hidden font-sans pt-20 text-slate-900">
        {/* Background matching homepage golden theme */}
        <div className="fixed inset-0 z-[-1]" style={{
          background: `radial-gradient(ellipse 200% 150% at 0% 100%, #F5EACE 0%, #F3E8C4 10%, #F0E5BA 18%, #EDE2B0 26%, #E5DDB8 35%, #cbd5e1 50%, #94a3b8 65%, #64748b 78%, #475569 90%, #1e293b 100%)`
        }}>
          {/* Subtle Noise Texture */}
          <div className="absolute inset-0 opacity-[0.04]" style={{ 
            backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E")` 
          }}></div>
          
          {/* Light Beam - Diagonal from Top-Left */}
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
        </div>

        {/* Content - Popup Style */}
        <div className="relative z-10 w-full max-w-md px-4 pointer-events-auto">
          {/* Decorative Corner Accents */}
          <div className="absolute top-0 left-4 w-10 h-10 border-t-2 border-l-2 border-white/30"></div>
          <div className="absolute top-0 right-4 w-10 h-10 border-t-2 border-r-2 border-white/30"></div>
          <div className="absolute bottom-0 left-4 w-10 h-10 border-b-2 border-l-2 border-white/30"></div>
          <div className="absolute bottom-0 right-4 w-10 h-10 border-b-2 border-r-2 border-white/30"></div>

          {/* Card */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            transition={{ duration: 0.4, type: "spring" }}
            className="backdrop-blur-2xl bg-white/5 border border-white/10 shadow-2xl p-8"
          >
            {/* Icon */}
            <div className="text-center mb-6">
              <motion.div
                initial={{ scale: 0, rotate: -180 }}
                animate={{ scale: 1, rotate: 0 }}
                transition={{ delay: 0.2, type: "spring", stiffness: 150 }}
                className="inline-flex items-center justify-center w-16 h-16 bg-white/20 backdrop-blur-md shadow-xl mb-4 relative border border-white/30"
              >
                <Lock className="w-8 h-8 text-slate-900 relative z-10" />
              </motion.div>
              
              <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-slate-900 mb-2">
                Authentication Required
              </h1>
              <p className="text-slate-700 text-xs font-medium">
                Access to Transcription System
              </p>
            </div>

            {/* Info Box */}
            <div className="bg-white/20 backdrop-blur-md border border-white/30 p-5 mb-6 shadow-sm">
              <div className="flex items-start gap-3 mb-4">
                <div className="flex-shrink-0 mt-0.5">
                  <ShieldAlert className="w-4 h-4 text-slate-900" />
                </div>
                <div>
                  <h3 className="font-semibold text-slate-900 text-sm mb-1">Secure Access Only</h3>
                  <p className="text-slate-800 text-xs leading-relaxed">
                    The transcription module is protected to ensure data security and maintain the integrity of the Pak Journal Archive. Please sign in to access AI-powered transcription features.
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 mt-0.5">
                  <Radio className="w-4 h-4 text-slate-900" />
                </div>
                <div>
                  <h3 className="font-semibold text-slate-900 text-sm mb-1">What You'll Get</h3>
                  <ul className="text-slate-800 text-xs space-y-0.5">
                    <li>• OpenAI Whisper AI transcription</li>
                    <li>• Urdu language support</li>
                    <li>• Real-time processing</li>
                    <li>• Archive management</li>
                  </ul>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="space-y-3">
              <button
                onClick={() => navigate('/login')}
                className="w-full backdrop-blur-xl bg-slate-900/80 hover:bg-black/90 text-white font-bold py-3 shadow-xl hover:shadow-2xl transition-all duration-300 border border-white/20 group"
              >
                <span className="flex items-center justify-center text-xs tracking-widest uppercase">
                  Sign In to Continue
                  <ArrowRight className="ml-2 group-hover:translate-x-1 transition-transform" size={14} />
                </span>
              </button>

              <button
                onClick={() => navigate('/')}
                className="w-full backdrop-blur-xl bg-white/20 hover:bg-white/30 text-slate-900 font-semibold py-3 shadow-lg transition-all duration-300 border border-white/30"
              >
                <span className="flex items-center justify-center text-xs tracking-widest uppercase">
                  <Home className="mr-2" size={14} />
                  Back to Home
                </span>
              </button>
            </div>
          </motion.div>
        </div>

        {/* Decorative Info */}
        <div className="absolute bottom-8 left-8 text-slate-900/40 text-xs hidden md:block pointer-events-none">
          <p className="font-semibold">Pak Journal Archive 77</p>
          <p className="text-[10px] mt-1">Secure Access • Protected Content</p>
        </div>
      </div>
    );
  }

  return children;
};

export default ProtectedRoute;
