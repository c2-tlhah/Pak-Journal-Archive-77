import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { motion } from 'framer-motion';
import { User, Lock, Mail, ArrowRight, Eye, EyeOff, Radio } from 'lucide-react';
import GoldenBackground from '../components/GoldenBackground';
import ThreeJsSphere from '../components/ThreeJsSphere';

const Login = () => {
  const navigate = useNavigate();
  const { login, signup } = useAuth();
  const [isLogin, setIsLogin] = useState(true);
  const [showPassword, setShowPassword] = useState(false);
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: ''
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const toggleMode = () => {
    setIsLogin(!isLogin);
    setError('');
    setFormData({
      username: '',
      email: '',
      password: ''
    });
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    // Validation
    if (isLogin) {
      if (!formData.email || !formData.password) {
        setError('Please fill in all fields');
        setLoading(false);
        return;
      }
      // Attempt login
      const result = await login(formData.email, formData.password);
      if (result.success) {
        navigate('/');
      } else {
        setError(result.error);
      }
    } else {
      if (!formData.username || !formData.email || !formData.password) {
        setError('Please fill in all fields');
        setLoading(false);
        return;
      }
      
      // Username validation
      const usernameRegex = /^[a-zA-Z0-9_]{3,20}$/;
      if (!usernameRegex.test(formData.username)) {
        setError('Username must be 3-20 characters and contain only letters, numbers, and underscores');
        setLoading(false);
        return;
      }

      // Password validation
      if (formData.password.length < 8) {
        setError('Password must be at least 8 characters');
        setLoading(false);
        return;
      }
      if (!/[A-Z]/.test(formData.password)) {
        setError('Password must contain at least one uppercase letter');
        setLoading(false);
        return;
      }
      if (!/[a-z]/.test(formData.password)) {
        setError('Password must contain at least one lowercase letter');
        setLoading(false);
        return;
      }
      if (!/[0-9]/.test(formData.password)) {
        setError('Password must contain at least one number');
        setLoading(false);
        return;
      }
      if (!/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>/?]/.test(formData.password)) {
        setError('Password must contain at least one special character');
        setLoading(false);
        return;
      }

      // Attempt signup
      const result = await signup(formData.username, formData.email, formData.password);
      if (result.success) {
        navigate('/');
      } else {
        setError(result.error);
      }
    }
    
    setLoading(false);
  };

  const handleBackToHome = () => {
    navigate('/');
  };

  return (
    <div className="min-h-screen w-full flex items-center justify-center font-sans text-slate-900 selection:bg-amber-300 relative overflow-hidden p-4 pt-24">
      
      {/* Background - Without Digital Globe */}
      <div className="fixed inset-0 z-[-1]" style={{
        background: `radial-gradient(ellipse 200% 150% at 0% 100%, #F5EACE 0%, #F3E8C4 10%, #F0E5BA 18%, #EDE2B0 26%, #E5DDB8 35%, #cbd5e1 50%, #94a3b8 65%, #64748b 78%, #475569 90%, #1e293b 100%)`
      }}>
        {/* Subtle Noise Texture */}
        <div className="absolute inset-0 opacity-[0.04]" style={{ 
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E")` 
        }}></div>
        
        {/* Light Beam */}
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

      {/* Main Floating Card with Form and Image */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="w-full max-w-5xl relative z-10 my-8"
      >
        {/* Main Transparent Card with Sharp Corners */}
        <div className="relative backdrop-blur-2xl bg-white/10 border border-white/20 shadow-2xl overflow-hidden flex flex-col lg:flex-row">
          {/* Corner Accents */}
          <div className="absolute top-0 left-0 w-16 h-16 border-t-2 border-l-2 border-amber-400/40 z-20"></div>
          <div className="absolute top-0 right-0 w-16 h-16 border-t-2 border-r-2 border-amber-400/40 z-20"></div>
          <div className="absolute bottom-0 left-0 w-16 h-16 border-b-2 border-l-2 border-amber-400/40 z-20"></div>
          <div className="absolute bottom-0 right-0 w-16 h-16 border-b-2 border-r-2 border-amber-400/40 z-20"></div>

          {/* LEFT SIDE - FORM SECTION */}
          <div className="w-full lg:w-1/2 p-8 sm:p-12 relative z-10">
            <div className="w-full max-w-md mx-auto">

              {/* Logo */}
              <div className="flex items-center gap-3 mb-8">
                <img 
                  src={`${import.meta.env.BASE_URL}logo.png`}
                  alt="Archive Logo" 
                  className="h-12 w-auto"
                />
              </div>

              <div className="mb-8">
                <h1 className="text-3xl font-extrabold mb-2 text-slate-900">
                    {isLogin ? 'Welcome back' : 'Start preserving history'}
                </h1>
                <p className="text-slate-700 font-medium text-sm">
                    {isLogin ? 'Enter your details to access the archive.' : 'Create your account to contribute to the archive.'}
                </p>
              </div>

            {/* Error Message */}
            {error && (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="mb-6 p-4 bg-red-50/80 backdrop-blur-sm border border-red-300 text-red-700 text-sm"
              >
                <p className="font-medium">{error}</p>
              </motion.div>
            )}

            <form className="space-y-5" onSubmit={handleSubmit}>
              
              {/* Username Field (Sign Up Only) */}
              {!isLogin && (
                <div className="group space-y-1.5">
                  <label className="text-xs font-bold text-slate-700 uppercase tracking-wider ml-1 group-focus-within:text-amber-600 transition-colors">Username</label>
                  <input 
                    type="text"
                    name="username"
                    value={formData.username}
                    onChange={handleChange}
                    placeholder="e.g. journalist123"
                    className="w-full px-4 py-3 bg-white/60 backdrop-blur-sm border border-white/40 text-slate-900 placeholder:text-slate-500 focus:outline-none focus:bg-white/80 focus:border-amber-400/60 focus:ring-2 focus:ring-amber-400/20 transition-all"
                    required={!isLogin}
                  />
                </div>
              )}

              {/* Email Field */}
              <div className="group space-y-1.5">
                <label className="text-xs font-bold text-slate-700 uppercase tracking-wider ml-1 group-focus-within:text-amber-600 transition-colors">Email Address</label>
                <input 
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  placeholder="name@example.com"
                  className="w-full px-4 py-3 bg-white/60 backdrop-blur-sm border border-white/40 text-slate-900 placeholder:text-slate-500 focus:outline-none focus:bg-white/80 focus:border-amber-400/60 focus:ring-2 focus:ring-amber-400/20 transition-all"
                  required
                />
              </div>

              {/* Password Field */}
              <div className="group space-y-1.5">
                <label className="text-xs font-bold text-slate-700 uppercase tracking-wider ml-1 group-focus-within:text-amber-600 transition-colors">Password</label>
                <div className="relative">
                  <input 
                    type={showPassword ? "text" : "password"}
                    name="password"
                    value={formData.password}
                    onChange={handleChange}
                    placeholder="••••••••"
                    className="w-full px-4 py-3 bg-white/60 backdrop-blur-sm border border-white/40 text-slate-900 placeholder:text-slate-500 focus:outline-none focus:bg-white/80 focus:border-amber-400/60 focus:ring-2 focus:ring-amber-400/20 transition-all pr-12"
                    required
                  />
                  <button 
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-500 hover:text-amber-600 transition-colors p-1"
                  >
                    {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                  </button>
                </div>
                {!isLogin && (
                  <p className="text-xs text-slate-600 ml-1 mt-1">Minimum 6 characters required</p>
                )}
              </div>

              {/* Submit Button */}
              <button 
                type="submit"
                disabled={loading}
                className="group w-full py-3.5 bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-600 hover:to-amber-700 text-white font-bold transition-all shadow-xl shadow-amber-500/20 hover:shadow-amber-600/30 active:scale-[0.98] flex items-center justify-center gap-2 mt-6 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <>
                    <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    <span>{isLogin ? 'Signing In...' : 'Creating...'}</span>
                  </>
                ) : (
                  <>
                    <span>{isLogin ? 'Access Archive' : 'Create Account'}</span>
                    <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
                  </>
                )}
              </button>
              
            </form>

            <p className="text-center text-sm font-medium text-slate-700 mt-6">
              {isLogin ? "New to Archive? " : "Already have an account? "} 
              <button 
                onClick={() => {
                  setIsLogin(!isLogin);
                  setError('');
                }}
                className="text-amber-600 font-bold hover:text-amber-700 hover:underline transition-all ml-1"
              >
                {isLogin ? "Create free account" : "Sign in now"}
              </button>
            </p>

              {/* Back to Home */}
              <div className="text-center mt-4 pt-4 border-t border-white/20">
                <button
                  onClick={() => navigate('/')}
                  className="text-slate-600 hover:text-slate-800 text-xs font-medium transition-colors inline-flex items-center gap-1"
                >
                  <ArrowRight size={14} className="rotate-180" />
                  Back to Home
                </button>
              </div>

            </div>
          </div>

          {/* RIGHT SIDE - ANIMATED SPHERE SECTION */}
          <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-amber-100/80 via-orange-50/60 to-slate-100/80 relative overflow-hidden items-center justify-center flex-col p-0">
            
            {/* Three.js 3D Sphere - Full Container */}
            <div className="w-full h-full absolute inset-0">
              <ThreeJsSphere />
            </div>

            {/* Slogan Below Sphere */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.5 }}
              className="relative z-10 text-center mt-auto mb-8 px-8"
            >
              <h2 className="text-2xl font-bold text-slate-800 mb-3 leading-tight drop-shadow-lg">
                Preserving History, <br/>
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-amber-600 to-amber-500">One Archive at a Time</span>
              </h2>
              <p className="text-slate-700 text-sm leading-relaxed max-w-sm mx-auto drop-shadow-md">
                Digitizing Pakistan's journalistic heritage with cutting-edge AI technology.
              </p>
            </motion.div>

          </div>

        </div>
      </motion.div>
    </div>
  );
};

export default Login;