import { motion } from 'framer-motion';
import { Link, useLocation } from 'react-router-dom';
import { Radio, FileText, Info, LogIn, UserPlus, User, LogOut } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useState } from 'react';

const Navbar = () => {
  const location = useLocation();
  const { user, isAuthenticated, logout } = useAuth();
  const [showUserMenu, setShowUserMenu] = useState(false);

  const navItems = [
    { name: 'Home', path: '/', icon: Radio },
    { name: 'Transcribe', path: '/transcribe', icon: FileText },
    { name: 'About', path: '/about', icon: Info },
  ];

  return (
    <motion.nav
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      className="fixed top-0 left-0 right-0 z-50"
    >
      <div className="w-full backdrop-blur-2xl bg-slate-950/60 border-b border-slate-800/50 shadow-lg">
        <div className="max-w-7xl mx-auto px-8 py-4">
          <div className="flex items-center justify-between">
            {/* Logo with News Icon */}
            <Link to="/">
              <motion.div
                className="flex items-center gap-3"
                whileHover={{ scale: 1.03 }}
              >
                <img 
                  src="/logo.png" 
                  alt="PAK NEWS JOURNAL" 
                  className="h-12 w-auto object-contain"
                />
                <div>
                  <div className="text-xl font-bold text-white tracking-tight">
                    Pak Journal Archive 77
                  </div>
                  <div className="text-[10px] text-slate-400 tracking-wider uppercase">
                    Archive Transcription System
                  </div>
                </div>
              </motion.div>
            </Link>

            {/* Nav Items */}
            <div className="flex items-center gap-3">
              {navItems.map((item) => {
                const isActive = location.pathname === item.path;
                const Icon = item.icon;
                return (
                  <Link key={item.path} to={item.path}>
                    <motion.div
                      className={`px-5 py-2.5 font-semibold transition-all duration-300 flex items-center gap-2 ${
                        isActive
                          ? 'bg-gradient-to-br from-white to-slate-100 text-slate-900 shadow-lg shadow-slate-300/50 border border-slate-200'
                          : 'text-slate-300 hover:text-white bg-slate-800/40 hover:bg-slate-800/60'
                      }`}
                      whileHover={{ scale: 1.05, y: -2 }}
                      whileTap={{ scale: 0.98 }}
                    >
                      <Icon className="w-4 h-4" />
                      {item.name}
                    </motion.div>
                  </Link>
                );
              })}

              {/* Auth Buttons */}
              {!isAuthenticated ? (
                <>
                  <Link to="/login">
                    <motion.div
                      className={`px-5 py-2.5 font-semibold transition-all duration-300 flex items-center gap-2 ${
                        location.pathname === '/login'
                          ? 'bg-gradient-to-br from-white to-slate-100 text-slate-900 shadow-lg shadow-slate-300/50 border border-slate-200'
                          : 'text-slate-300 hover:text-white bg-slate-800/40 hover:bg-slate-800/60'
                      }`}
                      whileHover={{ scale: 1.05, y: -2 }}
                      whileTap={{ scale: 0.98 }}
                    >
                      <LogIn className="w-4 h-4" />
                      Login
                    </motion.div>
                  </Link>
                  <Link to="/signup">
                    <motion.div
                      className={`px-5 py-2.5 font-semibold transition-all duration-300 flex items-center gap-2 ${
                        location.pathname === '/signup'
                          ? 'bg-gradient-to-br from-white to-slate-100 text-slate-900 shadow-lg shadow-slate-300/50 border border-slate-200'
                          : 'text-slate-300 hover:text-white bg-slate-800/40 hover:bg-slate-800/60'
                      }`}
                      whileHover={{ scale: 1.05, y: -2 }}
                      whileTap={{ scale: 0.98 }}
                    >
                      <UserPlus className="w-4 h-4" />
                      Sign Up
                    </motion.div>
                  </Link>
                </>
              ) : (
                <div className="relative">
                  <motion.button
                    onClick={() => setShowUserMenu(!showUserMenu)}
                    className="px-5 py-2.5 font-semibold bg-slate-800/60 hover:bg-slate-800/80 text-white transition-all duration-300 flex items-center gap-2"
                    whileHover={{ scale: 1.05, y: -2 }}
                    whileTap={{ scale: 0.98 }}
                  >
                    <User className="w-4 h-4" />
                    {user?.username}
                  </motion.button>

                  {/* User Dropdown Menu */}
                  {showUserMenu && (
                    <motion.div
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="absolute right-0 mt-2 w-56 backdrop-blur-2xl bg-slate-900/95 border border-slate-700/50 rounded-lg shadow-2xl overflow-hidden z-50"
                    >
                      <div className="p-4 border-b border-slate-700/50">
                        <p className="text-sm text-slate-400">Signed in as</p>
                        <p className="text-white font-semibold truncate">{user?.email}</p>
                        <p className="text-xs text-blue-400 mt-1 uppercase">{user?.role}</p>
                      </div>
                      <button
                        onClick={() => {
                          logout();
                          setShowUserMenu(false);
                        }}
                        className="w-full px-4 py-3 text-left text-red-400 hover:bg-red-500/10 transition-colors flex items-center gap-2"
                      >
                        <LogOut className="w-4 h-4" />
                        Logout
                      </button>
                    </motion.div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </motion.nav>
  );
};

export default Navbar;
