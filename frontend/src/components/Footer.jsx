import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { Radio, FileText, Info, Github, Mail, MapPin, Phone, Globe, ArrowUpRight } from 'lucide-react';
import { useState } from 'react';

const Footer = () => {
  const [hoveredLink, setHoveredLink] = useState(null);

  const quickLinks = [
    { name: 'Home', path: '/', icon: Radio },
    { name: 'Transcribe', path: '/transcribe', icon: FileText },
    { name: 'About', path: '/about', icon: Info },
  ];

  const features = [
    'AI-Powered Transcription',
    'Urdu Language Support',
    'Real-time Processing',
    'Secure Database Storage',
  ];

  const contactInfo = [
    { icon: MapPin, text: 'Islamabad, Pakistan' },
    { icon: Mail, text: 'contact@pakjournal.pk' },
    { icon: Phone, text: '+92 (51) 1234-567' },
  ];

  return (
    <footer className="relative bg-slate-900 text-slate-300 overflow-hidden border-t border-slate-800/50">
      {/* Animated Background Elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {/* Floating Orbs */}
        <motion.div
          className="absolute top-20 left-10 w-64 h-64 rounded-full bg-amber-500/10 blur-3xl"
          animate={{
            y: [0, 30, 0],
            scale: [1, 1.1, 1],
          }}
          transition={{
            duration: 8,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        />
        <motion.div
          className="absolute bottom-20 right-20 w-80 h-80 rounded-full bg-amber-600/8 blur-3xl"
          animate={{
            y: [0, -40, 0],
            scale: [1, 1.2, 1],
          }}
          transition={{
            duration: 10,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        />
        
        {/* Grid Pattern */}
        <div className="absolute inset-0 opacity-[0.02]" style={{
          backgroundImage: `linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px),
                           linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)`,
          backgroundSize: '50px 50px'
        }} />
      </div>

      <div className="relative z-10 max-w-7xl mx-auto px-4 py-6 md:px-8 md:py-8">
        {/* Top Section */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
          
          {/* Brand Section */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="lg:col-span-1"
          >
            <Link to="/">
              <motion.div 
                className="flex items-center gap-2 mb-3 group cursor-pointer"
                whileHover={{ scale: 1.02 }}
              >
                <img 
                  src="/logo.png" 
                  alt="PAK NEWS JOURNAL" 
                  className="h-8 w-auto object-contain opacity-90 group-hover:opacity-100 transition-opacity"
                />
                <div>
                  <div className="text-sm font-bold text-white">
                    Pak Journal Archive
                  </div>
                  <div className="text-[9px] text-amber-400 uppercase tracking-wider">
                    Since 2020
                  </div>
                </div>
              </motion.div>
            </Link>
            <p className="text-xs text-slate-400 leading-snug mb-2">
              Preserving Pakistan's broadcast heritage through cutting-edge AI transcription technology.
            </p>
            <div className="flex gap-2">
              <motion.a
                href="https://github.com"
                target="_blank"
                rel="noopener noreferrer"
                className="w-8 h-8 rounded-full bg-slate-800/50 border border-slate-700/50 flex items-center justify-center hover:bg-slate-700/50 hover:border-amber-500/50 transition-all"
                whileHover={{ scale: 1.1, rotate: 5 }}
                whileTap={{ scale: 0.95 }}
              >
                <Github size={16} />
              </motion.a>
              <motion.a
                href="mailto:contact@pakjournal.pk"
                className="w-8 h-8 rounded-full bg-slate-800/50 border border-slate-700/50 flex items-center justify-center hover:bg-slate-700/50 hover:border-amber-500/50 transition-all"
                whileHover={{ scale: 1.1, rotate: -5 }}
                whileTap={{ scale: 0.95 }}
              >
                <Mail size={16} />
              </motion.a>
              <motion.a
                href="#"
                className="w-8 h-8 rounded-full bg-slate-800/50 border border-slate-700/50 flex items-center justify-center hover:bg-slate-700/50 hover:border-amber-500/50 transition-all"
                whileHover={{ scale: 1.1, rotate: 5 }}
                whileTap={{ scale: 0.95 }}
              >
                <Globe size={16} />
              </motion.a>
            </div>
          </motion.div>

          {/* Quick Links */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.1 }}
          >
            <h3 className="text-white font-bold text-xs uppercase tracking-wider mb-3 flex items-center gap-2">
              <span className="w-4 h-0.5 bg-amber-500"></span>
              Quick Links
            </h3>
            <ul className="space-y-1.5">
              {quickLinks.map((link, index) => {
                const Icon = link.icon;
                return (
                  <li key={index}>
                    <Link 
                      to={link.path}
                      onMouseEnter={() => setHoveredLink(link.name)}
                      onMouseLeave={() => setHoveredLink(null)}
                    >
                      <motion.div
                        className="flex items-center gap-2 text-slate-400 hover:text-amber-400 transition-colors group"
                        whileHover={{ x: 5 }}
                      >
                        <Icon size={14} className="opacity-50 group-hover:opacity-100" />
                        <span className="text-xs">{link.name}</span>
                        <ArrowUpRight 
                          size={12} 
                          className={`opacity-0 group-hover:opacity-100 transition-opacity ${
                            hoveredLink === link.name ? 'rotate-45' : ''
                          }`}
                        />
                      </motion.div>
                    </Link>
                  </li>
                );
              })}
            </ul>
          </motion.div>

          {/* Features */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            <h3 className="text-white font-bold text-xs uppercase tracking-wider mb-3 flex items-center gap-2">
              <span className="w-4 h-0.5 bg-amber-500"></span>
              Features
            </h3>
            <ul className="space-y-1.5">
              {features.map((feature, index) => (
                <motion.li
                  key={index}
                  className="flex items-center gap-2 text-xs text-slate-400"
                  whileHover={{ x: 5 }}
                >
                  <motion.span
                    className="w-1 h-1 rounded-full bg-amber-500"
                    animate={{
                      scale: [1, 1.3, 1],
                      opacity: [0.5, 1, 0.5],
                    }}
                    transition={{
                      duration: 2,
                      repeat: Infinity,
                      delay: index * 0.2,
                    }}
                  />
                  {feature}
                </motion.li>
              ))}
            </ul>
          </motion.div>

          {/* Contact */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.3 }}
          >
            <h3 className="text-white font-bold text-xs uppercase tracking-wider mb-3 flex items-center gap-2">
              <span className="w-4 h-0.5 bg-amber-500"></span>
              Contact
            </h3>
            <ul className="space-y-2">
              {contactInfo.map((item, index) => {
                const Icon = item.icon;
                return (
                  <motion.li
                    key={index}
                    className="flex items-start gap-2 text-xs text-slate-400"
                    whileHover={{ x: 5 }}
                  >
                    <motion.div
                      className="mt-0.5"
                      whileHover={{ rotate: 360 }}
                      transition={{ duration: 0.6 }}
                    >
                      <Icon size={14} className="text-amber-500" />
                    </motion.div>
                    <span>{item.text}</span>
                  </motion.li>
                );
              })}
            </ul>
          </motion.div>
        </div>

        {/* Divider */}
        <motion.div
          className="relative h-px bg-gradient-to-r from-transparent via-slate-700 to-transparent mb-4"
          initial={{ scaleX: 0 }}
          whileInView={{ scaleX: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 1 }}
        />

        {/* Bottom Section */}
        <motion.div
          className="flex flex-col md:flex-row justify-between items-center gap-2"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.4 }}
        >
          <div className="text-xs text-slate-500 flex items-center gap-2">
            <motion.span
              animate={{
                opacity: [0.5, 1, 0.5],
              }}
              transition={{
                duration: 2,
                repeat: Infinity,
              }}
            >
              ©
            </motion.span>
            {new Date().getFullYear()} Pak Journal Archive. All rights reserved.
          </div>
          
          <div className="flex gap-4 text-xs">
            <motion.a
              href="#"
              className="text-slate-500 hover:text-amber-400 transition-colors"
              whileHover={{ y: -2 }}
            >
              Privacy Policy
            </motion.a>
            <motion.a
              href="#"
              className="text-slate-500 hover:text-amber-400 transition-colors"
              whileHover={{ y: -2 }}
            >
              Terms of Service
            </motion.a>
          </div>
        </motion.div>
      </div>
    </footer>
  );
};

export default Footer;
