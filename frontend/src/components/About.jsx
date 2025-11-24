import { motion } from 'framer-motion';

const About = () => {
  return (
    <section
      id="about"
      className="min-h-screen flex items-center justify-center px-6 py-20"
    >
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.8 }}
        className="max-w-4xl w-full"
      >
        {/* Glass Panel */}
        <div
          className="relative backdrop-blur-xl bg-white/5 rounded-2xl p-8 md:p-12
                     border border-white/10 shadow-2xl overflow-hidden"
          style={{
            boxShadow: '0 0 40px rgba(0, 242, 234, 0.1), inset 0 0 40px rgba(255, 0, 80, 0.05)'
          }}
        >
          {/* Gradient Border Effect */}
          <div className="absolute inset-0 rounded-2xl opacity-50 pointer-events-none"
               style={{
                 background: 'linear-gradient(135deg, rgba(0,242,234,0.1) 0%, rgba(255,0,80,0.1) 100%)',
               }}
          ></div>
          
          {/* Content */}
          <div className="relative z-10">
            <h2 className="text-4xl md:text-5xl font-bold mb-6 text-transparent bg-clip-text bg-gradient-to-r from-neon-cyan to-white">
              About the System
            </h2>
            
            <p className="text-lg text-gray-300 leading-relaxed mb-6">
              This is a cutting-edge <span className="text-neon-cyan font-semibold">Transcript Generation Module</span> designed 
              specifically for <span className="text-neon-magenta font-semibold">Urdu language</span> content. Powered by OpenAI's 
              Whisper AI model, it converts video and audio files into accurate, timestamped text transcriptions.
            </p>
            
            <p className="text-lg text-gray-300 leading-relaxed mb-6">
              Built with a futuristic, glassmorphic interface inspired by HUD systems and cyberpunk aesthetics, 
              the module provides real-time processing feedback and detailed system logs.
            </p>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8">
              <div className="backdrop-blur-sm bg-white/5 rounded-lg p-4 border border-neon-cyan/30">
                <h3 className="text-neon-cyan font-bold mb-2">AI-Powered</h3>
                <p className="text-sm text-gray-400">Whisper Tiny Model</p>
              </div>
              <div className="backdrop-blur-sm bg-white/5 rounded-lg p-4 border border-neon-magenta/30">
                <h3 className="text-neon-magenta font-bold mb-2">Urdu Native</h3>
                <p className="text-sm text-gray-400">Optimized for Urdu</p>
              </div>
              <div className="backdrop-blur-sm bg-white/5 rounded-lg p-4 border border-white/30">
                <h3 className="text-white font-bold mb-2">Real-Time</h3>
                <p className="text-sm text-gray-400">Live Progress Tracking</p>
              </div>
            </div>
          </div>
        </div>
      </motion.div>
    </section>
  );
};

export default About;
