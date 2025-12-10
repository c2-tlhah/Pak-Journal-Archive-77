import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import GoldenBackground from '../components/GoldenBackground';
import Footer from '../components/Footer';
import { Globe, Layers, Zap, Code } from 'lucide-react';

const TechIcon = ({ icon: Icon }) => (
  <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center text-slate-900 shadow-sm border border-white/30">
    <Icon size={16} />
  </div>
);

const Home = () => {
  return (
    <div className="relative min-h-[100dvh] w-full overflow-hidden text-slate-900 font-sans selection:bg-amber-300 flex flex-col">
      
      <GoldenBackground />

      {/* Main Content */}
      <main className="relative z-10 max-w-[1400px] mx-auto px-6 md:px-12 pt-32 md:pt-40 pb-20 flex-grow flex flex-col justify-center pointer-events-none w-full">
        <div className="max-w-2xl pointer-events-auto">
          
          <motion.h1 
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="text-5xl sm:text-6xl md:text-[5.5rem] font-medium tracking-tight text-slate-900 leading-[1.1] md:leading-[1.05] mb-8 md:mb-8 drop-shadow-sm"
          >
            Pak  Journal<br />
            Archive 77, <br />
            Transcription System
          </motion.h1>

          <motion.p 
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.4 }}
            className="text-lg sm:text-xl md:text-xl text-slate-800 max-w-lg leading-relaxed mb-10 md:mb-10 font-normal"
          >
            Advanced AI-powered transcription system for Urdu news archives. 
            Convert video content to searchable, editable text with precision.
          </motion.p>

          <motion.div 
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.6 }}
            className="flex flex-col sm:flex-row items-start space-y-6 sm:space-y-0 sm:space-x-6"
          >
            <Link to="/transcribe" className="w-full sm:w-auto">
              <button className="w-full sm:w-auto px-8 py-5 bg-slate-900 text-white text-sm font-bold tracking-widest rounded-full hover:bg-black transition-all shadow-2xl flex items-center justify-center group uppercase hover:scale-105 transform">
                Start Transcribing
                <svg className="ml-2 w-4 h-4 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </button>
            </Link>
            
            <Link to="/about" className="w-full sm:w-auto">
              <button className="w-full sm:w-auto px-8 py-5 bg-white/20 backdrop-blur-md text-slate-900 text-sm font-bold tracking-widest rounded-full hover:bg-white/30 transition-all shadow-xl border border-white/40 uppercase">
                Learn More
              </button>
            </Link>
          </motion.div>
          
          <motion.p 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.8, delay: 0.8 }}
            className="mt-12 md:mt-12 text-sm sm:text-sm text-slate-700 font-medium"
          >
            Powered by OpenAI Whisper • Urdu Language Support • Database Storage
          </motion.p>

        </div>
      </main>

      <Footer />
    </div>
  );
};

export default Home;
