import { motion } from 'framer-motion';

const Intro = () => {
  return (
    <motion.section
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.8 }}
      className="min-h-screen flex flex-col items-center justify-center relative overflow-hidden"
    >
      {/* Background Glow */}
      <div className="absolute inset-0 bg-gradient-radial from-neon-cyan/10 via-transparent to-transparent opacity-50 animate-glow-pulse"></div>
      
      {/* Content */}
      <div className="relative z-10 text-center px-6">
        <motion.h1
          className="text-6xl md:text-8xl font-bold mb-6 bg-gradient-to-r from-neon-cyan to-neon-magenta bg-clip-text text-transparent"
          initial={{ scale: 0.9 }}
          animate={{ scale: 1 }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          TRANSCRIPT
        </motion.h1>
        
        <motion.p
          className="text-xl md:text-2xl text-gray-400 mb-12 tracking-wide"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
        >
          AI-Powered Urdu Transcription
        </motion.p>
        
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6 }}
        >
          <button
            onClick={() => {
              document.getElementById('about').scrollIntoView({ behavior: 'smooth' });
            }}
            className="px-8 py-4 rounded-full bg-gradient-to-r from-neon-cyan to-neon-magenta text-white font-bold text-lg
                     hover:shadow-[0_0_30px_rgba(0,242,234,0.6)] transition-all duration-300 transform hover:scale-105"
          >
            Enter System
          </button>
        </motion.div>
      </div>
      
      {/* Noise Texture Overlay */}
      <div className="absolute inset-0 opacity-[0.03] pointer-events-none bg-noise"></div>
    </motion.section>
  );
};

export default Intro;
