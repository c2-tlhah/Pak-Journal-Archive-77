import { motion, AnimatePresence } from 'framer-motion';
import { Link, useLocation } from 'react-router-dom';
import { Radio, FileText, Info, LogIn, UserPlus, User, LogOut, Menu, X } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useState } from 'react';

const Navbar = () => {
  const location = useLocation();
  const { user, isAuthenticated, logout } = useAuth();
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

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
        <div className="max-w-7xl mx-auto px-4 md:px-8 py-4">
          <div className="flex items-center justify-between">
            {/* Logo with News Icon */}
            <Link to="/" className="z-50">
              <motion.div
                className="flex items-center gap-3"
                whileHover={{ scale: 1.03 }}
              >
                <img 
                  src="/Pak-Journal-Archive-77/logo.png" 
                  alt="PAK NEWS JOURNAL" 
                  className="h-8 md:h-12 w-auto object-contain"
                />
                <div>
                  <div className="text-lg md:text-xl font-bold text-white tracking-tight">
                    Pak Journal Archive 77
                  </div>
                  <div className="text-[8px] md:text-[10px] text-slate-400 tracking-wider uppercase hidden sm:block">
                    Archive Transcription System
                  </div>
                </div>
              </motion.div>
            </Link>

            {/* Desktop Nav Items */}
            <div className="hidden md:flex items-center gap-3">
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
                <Link to="/login">
                  <motion.div
                    className={`px-5 py-2.5 font-semibold transition-all duration-300 flex items-center gap-2 ${
                      location.pathname === '/login' || location.pathname === '/signup'
                        ? 'bg-gradient-to-br from-white to-slate-100 text-slate-900 shadow-lg shadow-slate-300/50 border border-slate-200'
                        : 'text-slate-300 hover:text-white bg-slate-800/40 hover:bg-slate-800/60'
                    }`}
                    whileHover={{ scale: 1.05, y: -2 }}
                    whileTap={{ scale: 0.98 }}
                  >
                    <LogIn className="w-4 h-4" />
                    Access Archive
                  </motion.div>
                </Link>
              ) : (
                <div className="relative">
                  <motion.button
                    onClick={() => setShowUserMenu(!showUserMenu)}
                    className="px-4 py-2 font-semibold bg-slate-800/60 hover:bg-slate-800/80 text-white transition-all duration-300 flex items-center gap-3 rounded-full pr-6"
                    whileHover={{ scale: 1.05, y: -2 }}
                    whileTap={{ scale: 0.98 }}
                  >
                    <div className="w-8 h-8 rounded-full bg-slate-700 overflow-hidden border border-slate-600">
                      {user?.profile_picture ? (
                        <img 
                          src={`http://localhost:5000/uploads/${user.profile_picture}`} 
                          alt={user.username} 
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center text-slate-400">
                          <User className="w-4 h-4" />
                        </div>
                      )}
                    </div>
                    {user?.username}
                  </motion.button>

                  {/* User Dropdown Menu */}
                  <AnimatePresence>
                    {showUserMenu && (
                      <motion.div
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                        className="absolute right-0 mt-2 w-56 backdrop-blur-2xl bg-slate-900/95 border border-slate-700/50 rounded-lg shadow-2xl overflow-hidden z-50"
                      >
                        <div className="p-4 border-b border-slate-700/50">
                          <p className="text-sm text-slate-400">Signed in as</p>
                          <p className="text-white font-semibold truncate">{user?.email}</p>
                          <p className="text-xs text-blue-400 mt-1 uppercase">{user?.role}</p>
                        </div>
                        <Link 
                          to="/profile"
                          className="w-full px-4 py-3 text-left text-slate-300 hover:bg-slate-800 hover:text-white transition-colors flex items-center gap-2"
                          onClick={() => setShowUserMenu(false)}
                        >
                          <User className="w-4 h-4" />
                          Profile
                        </Link>
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
                  </AnimatePresence>
                </div>
              )}
            </div>

            {/* Mobile Menu Button */}
            <div className="md:hidden z-50">
              <button
                onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                className="p-2 text-slate-300 hover:text-white transition-colors"
              >
                {isMobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
              </button>
            </div>
          </div>
        </div>

        {/* Mobile Menu Overlay */}
        <AnimatePresence>
          {isMobileMenuOpen && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="md:hidden border-t border-slate-800/50 bg-slate-950/95 backdrop-blur-xl overflow-hidden"
            >
              <div className="px-4 py-6 space-y-4">
                {navItems.map((item) => {
                  const isActive = location.pathname === item.path;
                  const Icon = item.icon;
                  return (
                    <Link 
                      key={item.path} 
                      to={item.path}
                      onClick={() => setIsMobileMenuOpen(false)}
                    >
                      <div
                        className={`px-4 py-3 rounded-lg font-semibold transition-all duration-300 flex items-center gap-3 mb-2 ${
                          isActive
                            ? 'bg-white/10 text-white border border-white/20'
                            : 'text-slate-400 hover:text-white hover:bg-white/5'
                        }`}
                      >
                        <Icon className="w-5 h-5" />
                        {item.name}
                      </div>
                    </Link>
                  );
                })}

                <div className="h-px bg-slate-800/50 my-4" />

                {!isAuthenticated ? (
                  <div className="space-y-3">
                    <Link to="/login" onClick={() => setIsMobileMenuOpen(false)}>
                      <div className="w-full px-4 py-3 rounded-lg font-semibold text-slate-300 hover:text-white hover:bg-white/5 flex items-center gap-3 border border-transparent">
                        <LogIn className="w-5 h-5" />
                        Login
                      </div>
                    </Link>
                    <Link to="/signup" onClick={() => setIsMobileMenuOpen(false)}>
                      <div className="w-full px-4 py-3 rounded-lg font-semibold bg-white text-slate-900 flex items-center gap-3 justify-center shadow-lg">
                        <UserPlus className="w-5 h-5" />
                        Sign Up
                      </div>
                    </Link>
                  </div>
                ) : (
                  <div className="space-y-3">
                    <div className="px-4 py-3 rounded-lg bg-slate-900/50 border border-slate-800">
                      <div className="flex items-center gap-3 mb-2">
                        <div className="w-8 h-8 rounded-full bg-slate-700 overflow-hidden border border-slate-600">
                          {user?.profile_picture ? (
                            <img 
                              src={`http://localhost:5000/uploads/${user.profile_picture}`} 
                              alt={user.username} 
                              className="w-full h-full object-cover"
                            />
                          ) : (
                            <div className="w-full h-full flex items-center justify-center text-slate-400">
                              <User className="w-4 h-4" />
                            </div>
                          )}
                        </div>
                        <span className="text-white font-semibold">{user?.username}</span>
                      </div>
                      <p className="text-xs text-slate-500 pl-11">{user?.email}</p>
                    </div>
                    <Link 
                      to="/profile"
                      onClick={() => setIsMobileMenuOpen(false)}
                      className="w-full px-4 py-3 rounded-lg font-semibold text-slate-300 hover:text-white hover:bg-white/5 flex items-center gap-3"
                    >
                      <User className="w-5 h-5" />
                      Profile
                    </Link>
                    <button
                      onClick={() => {
                        logout();
                        setIsMobileMenuOpen(false);
                      }}
                      className="w-full px-4 py-3 rounded-lg font-semibold text-red-400 hover:bg-red-500/10 flex items-center gap-3"
                    >
                      <LogOut className="w-5 h-5" />
                      Logout
                    </button>
                  </div>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.nav>
  );
};

export default Navbar;
