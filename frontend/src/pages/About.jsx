import { motion } from 'framer-motion';
import { Target, Heart, Database, Zap, Shield, Globe } from 'lucide-react';
import GoldenBackground from '../components/GoldenBackground';
import Footer from '../components/Footer';

const About = () => {
  const teamMembers = [
    { name: "Omer Farooq Khan", role: "Researcher", img: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400&auto=format&fit=crop&q=80" },
    { name: "Muhammad Talha Ramzan", role: "Researcher", img: "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=400&auto=format&fit=crop&q=80" },
    { name: "Zayyan Ahmad", role: "Researcher", img: "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=400&auto=format&fit=crop&q=80" },
    { name: "Mr. Ali Raza", role: "Supervisor", img: "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=400&auto=format&fit=crop&q=80" }
  ];

  return (
    <div className="relative min-h-screen overflow-hidden text-slate-900">
      <style>{`
        @keyframes fadeInUp {
          from { opacity: 0; transform: translateY(40px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .animate-fadeInUp {
          animation: fadeInUp 0.8s cubic-bezier(0.2, 0.8, 0.2, 1) forwards;
          opacity: 0;
        }
        .delay-100 { animation-delay: 0.1s; }
        .delay-200 { animation-delay: 0.2s; }
        .delay-300 { animation-delay: 0.3s; }
        .delay-400 { animation-delay: 0.4s; }

        .fluid-card {
          background: #ffffff;
          border: none;
          border-radius: 1.5rem;
          box-shadow: 0 15px 35px -5px rgba(0, 0, 0, 0.06), 0 10px 10px -5px rgba(0, 0, 0, 0.02);
          transition: transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.4s ease;
          overflow: hidden;
          position: relative;
        }
        
        .fluid-card:hover {
          transform: translateY(-8px) scale(1.01);
          box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.15);
          z-index: 10;
        }
        
        .fluid-card:hover img {
          transform: scale(1.08);
        }
        .fluid-card img {
          transition: transform 0.7s ease-out;
        }
      `}</style>
      
      <GoldenBackground />

      <div className="relative z-10 w-full pb-20">
        
        {/* 1. HERO SECTION */}
        <div className="max-w-[1200px] mx-auto px-6 md:px-12 pt-24 md:pt-32 mb-24 animate-fadeInUp">
          <div className="max-w-3xl">
            <div className="inline-block px-3 py-1 mb-6 rounded-full bg-amber-100 text-amber-800 text-xs font-bold tracking-widest uppercase">
              Our Mission
            </div>
            <h2 className="text-4xl md:text-6xl font-medium tracking-tight text-slate-900 mb-8 leading-tight">
              Preserving Pakistan's broadcast history <br/>
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-amber-600 to-amber-800">through AI-powered transcription.</span>
            </h2>
            <p className="text-xl text-slate-700 leading-relaxed max-w-2xl">
              Pak News Journal Archive was founded to unlock decades of Pakistan's media history trapped in video archives. We use cutting-edge AI to make them searchable and accessible.
            </p>
          </div>
        </div>

        {/* 2. OUR STORY */}
        <div className="max-w-[1200px] mx-auto px-6 md:px-12 mb-32">
          <div className="text-sm font-bold text-slate-500 uppercase tracking-widest mb-12 border-b border-slate-300 pb-4">Our Journey</div>

          {/* Story 1: Wide Image */}
          <div className="flex flex-col lg:flex-row items-start gap-12 mb-32 animate-fadeInUp delay-200">
            <div className="w-full lg:w-7/12">
              <div className="fluid-card h-[450px]">
                <img 
                  src="caset.jpg" 
                  alt="Video Archives and Tapes" 
                  className="w-full h-full object-cover"
                />
                <div className="absolute bottom-0 left-0 bg-white px-6 py-3 rounded-tr-2xl text-xs font-bold tracking-widest text-slate-900">EST. 2020</div>
              </div>
            </div>
            <div className="w-full lg:w-5/12 lg:pt-8">
              <h3 className="text-3xl font-bold text-slate-900 mb-4">A Vanishing Legacy</h3>
              <p className="text-slate-700 leading-relaxed text-lg mb-6">
                In archives across Pakistan, thousands of broadcast tapes from the last five decades sit deteriorating. These recordings contain invaluable moments of national history—news reports, interviews, cultural programs, and pivotal events.
              </p>
              <p className="text-slate-700 leading-relaxed text-lg">
                We realized that digitization alone wasn't enough. To make this content truly accessible, we needed to transcribe every word spoken in Urdu and English.
              </p>
            </div>
          </div>

          {/* Story 2: Tall Portrait */}
          <div className="flex flex-col lg:flex-row-reverse items-center gap-16 mb-32 animate-fadeInUp delay-300">
            <div className="w-full lg:w-5/12">
              <div className="fluid-card h-[550px] w-full lg:w-4/5 mx-auto">
                <img 
                  src="https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=800&auto=format&fit=crop&q=80" 
                  alt="Digital Technology and Data Processing" 
                  className="w-full h-full object-cover"
                />
              </div>
            </div>
            <div className="w-full lg:w-7/12">
              <h3 className="text-3xl font-bold text-slate-900 mb-4">Building the Technology</h3>
              <p className="text-slate-700 leading-relaxed text-lg mb-6">
                We developed a custom transcription pipeline using OpenAI's Whisper model, fine-tuned specifically for Urdu language nuances and Pakistani accents. Our system processes thousands of hours of video content with industry-leading accuracy.
              </p>
              <div className="grid grid-cols-2 gap-6 mt-8">
                <div className="bg-white p-6 rounded-2xl shadow-sm">
                  <div className="text-4xl font-bold text-amber-600 mb-1">98%</div>
                  <div className="text-xs font-bold text-slate-500 uppercase">Accuracy Rate</div>
                </div>
                <div className="bg-white p-6 rounded-2xl shadow-sm">
                  <div className="text-4xl font-bold text-amber-600 mb-1">24/7</div>
                  <div className="text-xs font-bold text-slate-500 uppercase">Processing</div>
                </div>
              </div>
            </div>
          </div>

          {/* Story 3: Full Width */}
          <div className="animate-fadeInUp delay-400">
            <div className="fluid-card h-[400px] w-full mb-8 relative group cursor-pointer">
              <img 
                src="https://images.unsplash.com/photo-1677756119517-756a188d2d94?w=1200&auto=format&fit=crop&q=80" 
                alt="AI and Machine Learning Technology" 
                className="w-full h-full object-cover"
              />
              <div className="absolute inset-0 bg-gradient-to-r from-slate-900/90 to-transparent flex items-center p-12">
                <div className="max-w-lg">
                  <div className="text-amber-400 font-bold text-lg mb-2">2024: Next Generation</div>
                  <h3 className="text-4xl font-bold text-white mb-4">AI Meets Heritage</h3>
                  <p className="text-slate-300 leading-relaxed text-lg">
                    With advanced language models and database integration, we've created a comprehensive archive system that makes decades of Pakistan's broadcast history instantly searchable.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 3. IMPACT NUMBERS */}
        <div className="w-full bg-slate-900 text-white py-24 mb-32">
          <div className="max-w-[1200px] mx-auto px-6 md:px-12">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-12 text-center">
              <div className="animate-fadeInUp delay-100">
                <div className="text-5xl font-bold text-amber-500 mb-2">500K+</div>
                <div className="text-sm uppercase tracking-widest font-bold text-slate-400">Hours Processed</div>
              </div>
              <div className="animate-fadeInUp delay-200">
                <div className="text-5xl font-bold text-amber-500 mb-2">50+</div>
                <div className="text-sm uppercase tracking-widest font-bold text-slate-400">Years of History</div>
              </div>
              <div className="animate-fadeInUp delay-300">
                <div className="text-5xl font-bold text-amber-500 mb-2">98%</div>
                <div className="text-sm uppercase tracking-widest font-bold text-slate-400">Transcription Accuracy</div>
              </div>
              <div className="animate-fadeInUp delay-400">
                <div className="text-5xl font-bold text-amber-500 mb-2">100%</div>
                <div className="text-sm uppercase tracking-widest font-bold text-slate-400">Secure & Private</div>
              </div>
            </div>
          </div>
        </div>

        {/* 4. CORE VALUES SECTION */}
        <div className="w-full py-20 mb-32" style={{
          background: 'linear-gradient(135deg, #1e293b 0%, #334155 50%, #475569 100%)'
        }}>
          <div className="max-w-[1200px] mx-auto px-6 md:px-12">
            <h2 className="text-4xl md:text-5xl font-bold text-amber-100 text-center mb-16 tracking-wide animate-fadeInUp">
              Core Values
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 md:gap-12">
              {/* Security First Card */}
              <div className="relative pb-12 animate-fadeInUp delay-100">
                <h3 className="text-2xl font-bold text-amber-300 mb-4 tracking-wider uppercase">Security First</h3>
                <p className="text-slate-200 text-base leading-relaxed">
                  Your data is encrypted and protected. Files are processed securely and deleted automatically after transcription is complete.
                </p>
                <span className="absolute bottom-0 left-0 text-4xl text-amber-400">→</span>
              </div>

              {/* Uncompromising Accuracy Card */}
              <div className="relative pb-12 animate-fadeInUp delay-200">
                <h3 className="text-2xl font-bold text-amber-300 mb-4 tracking-wider uppercase">Uncompromising Accuracy</h3>
                <p className="text-slate-200 text-base leading-relaxed">
                  Historical accuracy is paramount. We rigorously test our models to ensure every word is transcribed exactly as spoken, preserving the original context and meaning.
                </p>
                <span className="absolute bottom-0 left-1/2 transform -translate-x-1/2 text-4xl text-amber-400">→</span>
              </div>

              {/* Innovation Driven Card */}
              <div className="relative pb-12 animate-fadeInUp delay-300">
                <h3 className="text-2xl font-bold text-amber-300 mb-4 tracking-wider uppercase">Innovation Driven</h3>
                <p className="text-slate-200 text-base leading-relaxed">
                  We constantly push boundaries with cutting-edge AI technology, delivering faster and more accurate transcriptions every day.
                </p>
                <span className="absolute bottom-0 right-0 text-4xl text-amber-400">→</span>
              </div>
            </div>
          </div>
        </div>

        {/* 5. TEAM */}
        <div className="max-w-[1200px] mx-auto px-6 md:px-12 animate-fadeInUp">
          <div className="flex flex-col md:flex-row items-end justify-between mb-12 border-b border-slate-300 pb-6">
            <div>
              <h2 className="text-3xl md:text-4xl font-bold text-slate-900">Leadership Team</h2>
            </div>
          </div>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {teamMembers.map((member, i) => (
              <div key={i} className="group fluid-card p-0">
                <div className="h-80 overflow-hidden relative">
                  <img src={member.img} alt={member.name} className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110 grayscale group-hover:grayscale-0" />
                  <div className="absolute bottom-0 left-0 w-full bg-gradient-to-t from-black/80 to-transparent p-6 pt-12 translate-y-2 group-hover:translate-y-0 transition-transform">
                    <h4 className="text-lg font-bold text-white">{member.name}</h4>
                    <p className="text-amber-400 text-sm font-medium">{member.role}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>
      
      <Footer />
    </div>
  );
};

export default About;
