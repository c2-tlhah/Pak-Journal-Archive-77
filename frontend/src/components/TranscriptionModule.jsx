import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, Play, FileAudio, Copy, CheckCircle, XCircle, Loader2, FileText, Download, RefreshCw, Sparkles, Zap, Clock } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import GoldenBackground from './GoldenBackground';

const API_URL = 'http://localhost:5000/api';

const TranscriptionModule = () => {
  const { getAuthHeader } = useAuth();
  const [file, setFile] = useState(null);
  const [jobId, setJobId] = useState(null);
  const [status, setStatus] = useState('idle');
  const [transcript, setTranscript] = useState('');
  const [step, setStep] = useState('');
  const [liveLogs, setLiveLogs] = useState([]);
  const [isDragging, setIsDragging] = useState(false);
  const [copied, setCopied] = useState(false);
  const fileInputRef = useRef(null);

  // Load saved job ID on mount
  useEffect(() => {
    const savedJobId = localStorage.getItem('currentJobId');
    if (savedJobId) {
      setJobId(savedJobId);
      setStatus('processing'); // Assume processing until verified
      setLiveLogs(['Resuming job monitoring...']);
    }
  }, []);

  useEffect(() => {
    if (jobId && status === 'processing') {
      // Save job ID to localStorage
      localStorage.setItem('currentJobId', jobId);

      const interval = setInterval(async () => {
        try {
          const response = await fetch(`${API_URL}/status/${jobId}`, {
            headers: {
              ...getAuthHeader()
            }
          });

          if (!response.ok) {
            if (response.status === 404) {
              // Job not found (server restarted?), reset to idle
              console.warn("Job not found, resetting state");
              localStorage.removeItem('currentJobId');
              setJobId(null);
              setStatus('idle');
              setLiveLogs([]);
              clearInterval(interval);
              return;
            }
            throw new Error(`HTTP error! status: ${response.status}`);
          }

          const data = await response.json();
          
          if (data.status) {
            setStatus(data.status);
          }
          
          setStep(data.step || '');
          
          if (data.step) {
            setLiveLogs(prev => {
              const lastLog = prev[prev.length - 1];
              if (lastLog !== data.step) {
                return [...prev, data.step].slice(-4);
              }
              return prev;
            });
          }
          
          if (data.status === 'completed') {
            setTranscript(data.transcript);
            localStorage.removeItem('currentJobId'); // Clear saved job
            clearInterval(interval);
          } else if (data.status === 'failed') {
            localStorage.removeItem('currentJobId'); // Clear saved job
            clearInterval(interval);
          }
        } catch (error) {
          console.error('Error polling status:', error);
          // Don't reset on transient network errors, but maybe after X retries?
          // For now, let it keep trying or user can refresh.
        }
      }, 2000);
      
      return () => clearInterval(interval);
    }
  }, [jobId, status]);

  const handleFileSelect = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setStatus('idle');
      setTranscript('');
      setLiveLogs([]);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      setFile(droppedFile);
      setStatus('idle');
      setTranscript('');
      setLiveLogs([]);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleStartTranscription = async () => {
    if (!file) return;
    
    setStatus('processing');
    setLiveLogs(['Uploading file...']);
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const response = await fetch(`${API_URL}/transcribe`, {
        method: 'POST',
        headers: {
          ...getAuthHeader()
        },
        body: formData,
      });
      
      const data = await response.json();
      setJobId(data.job_id);
      setLiveLogs(prev => [...prev, `Job started: ${data.job_id}`]);
    } catch (error) {
      console.error('Error starting transcription:', error);
      setStatus('failed');
      setLiveLogs(prev => [...prev, `Error: ${error.message}`]);
    }
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(transcript);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const downloadTranscript = () => {
    const blob = new Blob([transcript], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `transcript_${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleReset = () => {
    setFile(null);
    setJobId(null);
    setStatus('idle');
    setTranscript('');
    setStep('');
    setLiveLogs([]);
  };

  return (
    <div className="relative min-h-screen overflow-hidden pt-32 pb-12 px-4">
      <GoldenBackground />
      
      <div className="relative z-10 max-w-7xl mx-auto">
        {/* Hero Section */}
        <motion.div
          initial={{ opacity: 0, y: -30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="text-center mb-16"
        >
          <h1 className="text-5xl md:text-6xl font-bold text-white mb-4 bg-gradient-to-r from-white via-blue-100 to-purple-200 bg-clip-text text-transparent drop-shadow-lg">
            AI Transcription Studio
          </h1>
          <p className="text-xl text-slate-300 max-w-2xl mx-auto">
            Transform audio and video into accurate Urdu text with cutting-edge AI technology
          </p>
        </motion.div>

        {/* Feature Cards */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3 }}
          className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-16"
        >
          {/* Card 1 */}
          <motion.div 
            className="group relative overflow-hidden rounded-3xl p-1"
            whileHover={{ y: -10, rotateX: 5, rotateY: 5 }}
            transition={{ type: "spring", stiffness: 300, damping: 20 }}
            style={{ perspective: 1000 }}
          >
            <div className="absolute inset-0 bg-gradient-to-br from-blue-400 to-blue-600 rounded-3xl blur opacity-40 group-hover:opacity-60 transition-opacity duration-500" />
            <div className="relative h-full bg-gradient-to-br from-slate-900 to-slate-800 rounded-[22px] p-8 border border-blue-500/30 shadow-2xl">
              <div className="absolute top-0 right-0 w-32 h-32 bg-blue-500/10 rounded-full blur-3xl -mr-16 -mt-16" />
              
              <motion.div 
                className="w-16 h-16 rounded-2xl bg-blue-500 flex items-center justify-center shadow-lg shadow-blue-500/40 mb-6"
                whileHover={{ rotate: [0, -10, 10, -10, 0] }}
                transition={{ duration: 0.5 }}
              >
                <FileAudio className="w-8 h-8 text-white" strokeWidth={2} />
              </motion.div>
              
              <h3 className="text-2xl font-bold text-white mb-3">Multiple Formats</h3>
              <p className="text-slate-400 leading-relaxed">
                Full support for MP4, AVI, MOV, MP3, WAV, and M4A file formats.
              </p>
            </div>
          </motion.div>
          
          {/* Card 2 */}
          <motion.div 
            className="group relative overflow-hidden rounded-3xl p-1"
            whileHover={{ y: -10, rotateX: 5, rotateY: 5 }}
            transition={{ type: "spring", stiffness: 300, damping: 20, delay: 0.1 }}
            style={{ perspective: 1000 }}
          >
            <div className="absolute inset-0 bg-gradient-to-br from-emerald-400 to-emerald-600 rounded-3xl blur opacity-40 group-hover:opacity-60 transition-opacity duration-500" />
            <div className="relative h-full bg-gradient-to-br from-slate-900 to-slate-800 rounded-[22px] p-8 border border-emerald-500/30 shadow-2xl">
              <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/10 rounded-full blur-3xl -mr-16 -mt-16" />
              
              <motion.div 
                className="w-16 h-16 rounded-2xl bg-emerald-500 flex items-center justify-center shadow-lg shadow-emerald-500/40 mb-6"
                whileHover={{ scale: [1, 1.1, 1] }}
                transition={{ duration: 0.3, repeat: 3 }}
              >
                <Zap className="w-8 h-8 text-white" strokeWidth={2} />
              </motion.div>
              
              <h3 className="text-2xl font-bold text-white mb-3">High Accuracy</h3>
              <p className="text-slate-400 leading-relaxed">
                State-of-the-art AI delivers 95%+ accuracy for Urdu transcription.
              </p>
            </div>
          </motion.div>
          
          {/* Card 3 */}
          <motion.div 
            className="group relative overflow-hidden rounded-3xl p-1"
            whileHover={{ y: -10, rotateX: 5, rotateY: 5 }}
            transition={{ type: "spring", stiffness: 300, damping: 20, delay: 0.2 }}
            style={{ perspective: 1000 }}
          >
            <div className="absolute inset-0 bg-gradient-to-br from-purple-400 to-purple-600 rounded-3xl blur opacity-40 group-hover:opacity-60 transition-opacity duration-500" />
            <div className="relative h-full bg-gradient-to-br from-slate-900 to-slate-800 rounded-[22px] p-8 border border-purple-500/30 shadow-2xl">
              <div className="absolute top-0 right-0 w-32 h-32 bg-purple-500/10 rounded-full blur-3xl -mr-16 -mt-16" />
              
              <motion.div 
                className="w-16 h-16 rounded-2xl bg-purple-500 flex items-center justify-center shadow-lg shadow-purple-500/40 mb-6"
                animate={{ rotate: [0, 360] }}
                transition={{ duration: 8, repeat: Infinity, ease: "linear" }}
              >
                <Clock className="w-8 h-8 text-white" strokeWidth={2} />
              </motion.div>
              
              <h3 className="text-2xl font-bold text-white mb-3">Lightning Fast</h3>
              <p className="text-slate-400 leading-relaxed">
                Get professional transcripts in minutes with optimized processing.
              </p>
            </div>
          </motion.div>
        </motion.div>

        {/* Main Card */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.4 }}
          className="relative bg-slate-900 rounded-[32px] border border-slate-700 shadow-[0_0_50px_-12px_rgba(0,0,0,0.8)] overflow-hidden"
          style={{
            boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(255, 255, 255, 0.1) inset'
          }}
        >
          <div className="absolute inset-0 bg-gradient-to-b from-slate-800/50 to-slate-900/50 pointer-events-none" />
          
          {/* Window Controls */}
          <div className="relative px-8 py-6 border-b border-slate-700/50 bg-slate-800/30 backdrop-blur-sm flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-red-500/80 border border-red-600/50" />
              <div className="w-3 h-3 rounded-full bg-yellow-500/80 border border-yellow-600/50" />
              <div className="w-3 h-3 rounded-full bg-green-500/80 border border-green-600/50" />
            </div>
            <div className="text-slate-500 text-sm font-medium">Transcription Studio</div>
            <div className="w-16" /> {/* Spacer for centering */}
          </div>

          {/* Main Content Area */}
          <div className="relative p-8 md:p-12">
            
            {/* Upload Section - Idle State */}
            {status === 'idle' && (
              <motion.div 
                initial={{ opacity: 0, scale: 0.95 }} 
                animate={{ opacity: 1, scale: 1 }} 
                transition={{ duration: 0.5 }}
                className="space-y-8"
              >
                <motion.div
                  className={`relative rounded-3xl p-16 transition-all duration-500 overflow-hidden cursor-pointer group ${
                    isDragging ? 'scale-[1.02] shadow-2xl' : ''
                  }`}
                  style={{
                    background: isDragging 
                      ? 'linear-gradient(135deg, rgba(59, 130, 246, 0.2) 0%, rgba(37, 99, 235, 0.15) 100%)'
                      : 'linear-gradient(135deg, rgba(30, 41, 59, 0.5) 0%, rgba(15, 23, 42, 0.7) 100%)',
                    border: isDragging ? '3px dashed rgba(59, 130, 246, 0.6)' : '3px dashed rgba(100, 116, 139, 0.3)',
                  }}
                  onDrop={handleDrop}
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onClick={handleUploadClick}
                  whileHover={{ scale: 1.01 }}
                >
                  <input ref={fileInputRef} type="file" accept="video/*,audio/*" onChange={handleFileSelect} className="hidden" />
                  
                  <motion.div 
                    className="absolute inset-0 bg-gradient-to-br from-blue-500/10 via-purple-500/5 to-transparent opacity-0 group-hover:opacity-100"
                    transition={{ duration: 0.3 }}
                  />
                  
                  <div className="relative flex flex-col items-center gap-8">
                    <motion.div
                      animate={{ 
                        y: isDragging ? [0, -12, 0] : [0, -6, 0],
                        scale: isDragging ? 1.15 : 1
                      }}
                      transition={{ 
                        duration: isDragging ? 0.8 : 2, 
                        repeat: Infinity,
                        ease: "easeInOut"
                      }}
                      className="relative"
                    >
                      <motion.div 
                        className="absolute inset-0 bg-blue-500/30 rounded-3xl blur-2xl"
                        animate={{ 
                          scale: [1, 1.3, 1],
                          opacity: [0.3, 0.6, 0.3]
                        }}
                        transition={{ duration: 2, repeat: Infinity }}
                      />
                      <div className="relative w-28 h-28 rounded-3xl bg-gradient-to-br from-blue-500/30 via-blue-600/20 to-purple-500/20 flex items-center justify-center border-2 border-blue-400/40 shadow-2xl shadow-blue-500/30">
                        <Upload className="w-14 h-14 text-blue-200" strokeWidth={2} />
                      </div>
                    </motion.div>

                    <div className="text-center space-y-3">
                      <motion.h3 
                        className="text-3xl text-white font-bold"
                        animate={{ scale: isDragging ? [1, 1.05, 1] : 1 }}
                        transition={{ duration: 0.3 }}
                      >
                        {isDragging ? '✨ Drop your file here' : 'Upload Your Media'}
                      </motion.h3>
                      <p className="text-slate-300 text-lg">
                        Drag and drop your file, or click to browse
                      </p>
                      <div className="flex flex-wrap justify-center gap-2 pt-2">
                        {['MP4', 'AVI', 'MOV', 'MP3', 'WAV', 'M4A'].map((format, idx) => (
                          <motion.span 
                            key={format}
                            initial={{ opacity: 0, scale: 0 }}
                            animate={{ opacity: 1, scale: 1 }}
                            transition={{ delay: 0.6 + idx * 0.1 }}
                            className="px-3 py-1 rounded-full bg-slate-700/50 text-slate-300 text-xs font-medium border border-slate-600/50"
                          >
                            {format}
                          </motion.span>
                        ))}
                      </div>
                    </div>

                    <motion.button 
                      onClick={(e) => {
                        e.stopPropagation();
                        handleUploadClick();
                      }}
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      className="px-10 py-4 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-500 hover:to-blue-600 text-white rounded-2xl font-semibold transition-all duration-300 border border-blue-400/30 shadow-xl shadow-blue-500/30 flex items-center gap-3 group"
                    >
                      <FileAudio className="w-5 h-5 group-hover:rotate-12 transition-transform duration-300" />
                      Choose File
                    </motion.button>
                  </div>
                </motion.div>

                <AnimatePresence>
                  {file && (
                    <motion.div 
                      initial={{ opacity: 0, y: 30, scale: 0.9 }} 
                      animate={{ opacity: 1, y: 0, scale: 1 }} 
                      exit={{ opacity: 0, y: -20, scale: 0.9 }} 
                      transition={{ type: "spring", stiffness: 200, damping: 20 }}
                    >
                      <div className="relative overflow-hidden flex flex-col md:flex-row items-center justify-between bg-gradient-to-r from-slate-800/70 via-slate-800/60 to-slate-900/70 rounded-2xl p-8 border border-slate-600/50 shadow-2xl backdrop-blur-xl gap-6">
                        <motion.div 
                          className="absolute inset-0 bg-gradient-to-r from-blue-500/10 to-purple-500/10"
                          animate={{ 
                            x: ['0%', '100%', '0%'],
                          }}
                          transition={{ duration: 3, repeat: Infinity }}
                        />
                        <div className="relative flex items-center gap-5 flex-1">
                          <motion.div 
                            className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500/30 to-purple-600/30 flex items-center justify-center border-2 border-blue-400/40 shadow-xl shadow-blue-500/20"
                            animate={{ rotate: [0, 5, -5, 0] }}
                            transition={{ duration: 2, repeat: Infinity }}
                          >
                            <FileAudio className="w-8 h-8 text-blue-200" strokeWidth={2} />
                          </motion.div>
                          <div className="flex-1">
                            <p className="text-white font-bold text-lg mb-1">{file.name}</p>
                            <div className="flex items-center gap-3 text-sm text-slate-300">
                              <span className="flex items-center gap-1">
                                <FileText className="w-4 h-4" />
                                {(file.size / 1024 / 1024).toFixed(2)} MB
                              </span>
                              <span className="text-slate-500">•</span>
                              <span className="px-2 py-0.5 rounded-md bg-blue-500/20 text-blue-300 text-xs font-medium">
                                Ready
                              </span>
                            </div>
                          </div>
                        </div>
                        <motion.button 
                          onClick={handleStartTranscription}
                          whileHover={{ scale: 1.05 }}
                          whileTap={{ scale: 0.95 }}
                          className="relative px-10 py-4 bg-gradient-to-r from-blue-600 via-blue-500 to-purple-600 hover:from-blue-500 hover:via-blue-400 hover:to-purple-500 text-white font-bold rounded-2xl transition-all duration-300 shadow-2xl shadow-blue-500/50 flex items-center gap-3 group overflow-hidden"
                        >
                          <motion.div 
                            className="absolute inset-0 bg-white/20"
                            animate={{ x: ['-100%', '100%'] }}
                            transition={{ duration: 1.5, repeat: Infinity, ease: "linear" }}
                          />
                          <Play className="relative w-5 h-5 fill-white group-hover:scale-110 transition-transform" />
                          <span className="relative">Start Transcription</span>
                        </motion.button>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            )}

            {/* Processing State */}
            {status === 'processing' && (
              <motion.div 
                initial={{ opacity: 0, scale: 0.9 }} 
                animate={{ opacity: 1, scale: 1 }} 
                className="flex flex-col items-center py-16 space-y-8"
              >
                <div className="relative">
                  <motion.div 
                    animate={{ rotate: 360 }} 
                    transition={{ duration: 2, repeat: Infinity, ease: 'linear' }} 
                    className="w-32 h-32 rounded-full border-4 border-slate-700/50 border-t-blue-500 border-r-purple-500"
                  />
                  <motion.div 
                    animate={{ rotate: -360 }} 
                    transition={{ duration: 3, repeat: Infinity, ease: 'linear' }} 
                    className="absolute inset-2 rounded-full border-4 border-slate-700/30 border-b-emerald-500"
                  />
                  <motion.div 
                    className="absolute inset-0 flex items-center justify-center"
                    animate={{ scale: [1, 1.1, 1] }}
                    transition={{ duration: 2, repeat: Infinity }}
                  >
                    <div className="w-16 h-16 rounded-full bg-gradient-to-br from-blue-500/30 to-purple-500/30 flex items-center justify-center border border-blue-400/30">
                      <Loader2 className="w-8 h-8 text-blue-300" />
                    </div>
                  </motion.div>
                  <motion.div 
                    className="absolute -inset-4 bg-blue-500/20 rounded-full blur-2xl"
                    animate={{ 
                      scale: [1, 1.3, 1],
                      opacity: [0.3, 0.6, 0.3]
                    }}
                    transition={{ duration: 2, repeat: Infinity }}
                  />
                </div>
                
                <div className="text-center space-y-3">
                  <motion.h3 
                    className="text-3xl font-bold text-white"
                    animate={{ opacity: [1, 0.7, 1] }}
                    transition={{ duration: 2, repeat: Infinity }}
                  >
                    Processing Your Media
                  </motion.h3>
                  <motion.p 
                    className="text-lg text-slate-300"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.3 }}
                  >
                    {step || 'Initializing AI transcription engine...'}
                  </motion.p>
                  <div className="flex items-center justify-center gap-2 pt-2">
                    <motion.div 
                      className="w-2 h-2 rounded-full bg-blue-500"
                      animate={{ scale: [1, 1.5, 1], opacity: [0.5, 1, 0.5] }}
                      transition={{ duration: 1, repeat: Infinity, delay: 0 }}
                    />
                    <motion.div 
                      className="w-2 h-2 rounded-full bg-purple-500"
                      animate={{ scale: [1, 1.5, 1], opacity: [0.5, 1, 0.5] }}
                      transition={{ duration: 1, repeat: Infinity, delay: 0.2 }}
                    />
                    <motion.div 
                      className="w-2 h-2 rounded-full bg-emerald-500"
                      animate={{ scale: [1, 1.5, 1], opacity: [0.5, 1, 0.5] }}
                      transition={{ duration: 1, repeat: Infinity, delay: 0.4 }}
                    />
                  </div>
                </div>

                {liveLogs.length > 0 && (
                  <motion.div 
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="w-full max-w-3xl bg-slate-950/70 rounded-2xl p-6 border border-slate-600/50 backdrop-blur-xl shadow-2xl"
                  >
                    <div className="flex items-center gap-2 mb-4 pb-3 border-b border-slate-700/50">
                      <div className="w-3 h-3 rounded-full bg-emerald-500 animate-pulse" />
                      <span className="text-slate-300 font-semibold text-sm">Live Progress</span>
                    </div>
                    <div className="space-y-3 font-mono text-sm">
                      {liveLogs.map((log, idx) => (
                        <motion.div 
                          key={idx} 
                          initial={{ opacity: 0, x: -20 }} 
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: idx * 0.1 }}
                          className="flex items-start gap-3 text-blue-300 bg-slate-900/50 rounded-lg px-4 py-3 border border-slate-700/30"
                        >
                          <Zap className="w-4 h-4 mt-0.5 flex-shrink-0 text-blue-400" />
                          <span className="flex-1">{log}</span>
                        </motion.div>
                      ))}
                    </div>
                  </motion.div>
                )}
              </motion.div>
            )}

            {/* Completed State */}
            {status === 'completed' && (
              <motion.div 
                initial={{ opacity: 0, scale: 0.9 }} 
                animate={{ opacity: 1, scale: 1 }} 
                transition={{ type: "spring", stiffness: 200 }}
                className="space-y-8"
              >
                <motion.div 
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ type: "spring", stiffness: 200, delay: 0.2 }}
                  className="flex flex-col items-center gap-4"
                >
                  <motion.div 
                    className="relative w-20 h-20 rounded-full bg-gradient-to-br from-emerald-500/30 to-green-600/30 flex items-center justify-center border-2 border-emerald-400/50 shadow-2xl shadow-emerald-500/30"
                    animate={{ 
                      boxShadow: [
                        '0 0 20px rgba(16, 185, 129, 0.3)',
                        '0 0 40px rgba(16, 185, 129, 0.5)',
                        '0 0 20px rgba(16, 185, 129, 0.3)'
                      ]
                    }}
                    transition={{ duration: 2, repeat: Infinity }}
                  >
                    <CheckCircle className="w-10 h-10 text-emerald-300" strokeWidth={2.5} />
                  </motion.div>
                  <div className="text-center">
                    <h3 className="text-3xl font-bold text-white mb-2">Transcription Complete! 🎉</h3>
                    <p className="text-slate-300">Your transcript is ready to download or copy</p>
                  </div>
                </motion.div>

                <motion.div 
                  initial={{ y: 20, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  transition={{ delay: 0.3 }}
                  className="relative bg-slate-950/60 rounded-2xl border border-slate-600/50 overflow-hidden backdrop-blur-xl shadow-2xl"
                >
                  <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-purple-500/5" />
                  
                  <div className="relative flex flex-wrap items-center justify-between px-8 py-5 border-b border-slate-600/50 bg-slate-900/50 gap-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500/30 to-purple-500/30 flex items-center justify-center border border-blue-400/30">
                        <FileText className="w-5 h-5 text-blue-200" />
                      </div>
                      <div>
                        <h4 className="text-white font-bold text-lg">Your Transcript</h4>
                        <p className="text-slate-400 text-sm">{transcript.length} characters</p>
                      </div>
                    </div>
                    <div className="flex gap-3">
                      <motion.button 
                        onClick={copyToClipboard}
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        className="flex items-center gap-2 px-5 py-2.5 bg-slate-700/70 hover:bg-slate-600/70 text-white rounded-xl transition-all duration-300 text-sm font-medium border border-slate-600/50 shadow-lg"
                      >
                        {copied ? (
                          <>
                            <CheckCircle className="w-4 h-4 text-emerald-400" />
                            Copied!
                          </>
                        ) : (
                          <>
                            <Copy className="w-4 h-4" />
                            Copy
                          </>
                        )}
                      </motion.button>
                      <motion.button 
                        onClick={downloadTranscript}
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white rounded-xl transition-all duration-300 text-sm font-medium border border-blue-400/30 shadow-xl shadow-blue-500/30"
                      >
                        <Download className="w-4 h-4" />
                        Download
                      </motion.button>
                    </div>
                  </div>
                  
                  <div className="relative p-8 text-slate-100 whitespace-pre-wrap max-h-[500px] overflow-y-auto leading-relaxed text-base" style={{
                    scrollbarWidth: 'thin',
                    scrollbarColor: 'rgba(100, 116, 139, 0.5) transparent'
                  }}>
                    {transcript}
                  </div>
                </motion.div>

                <motion.div 
                  initial={{ y: 20, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  transition={{ delay: 0.4 }}
                  className="flex justify-center pt-4"
                >
                  <motion.button 
                    onClick={handleReset}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    className="px-10 py-4 bg-gradient-to-r from-slate-700 to-slate-800 hover:from-slate-600 hover:to-slate-700 text-white rounded-2xl font-semibold transition-all duration-300 border border-slate-600/50 shadow-xl flex items-center gap-3 group"
                  >
                    <RefreshCw className="w-5 h-5 group-hover:rotate-180 transition-transform duration-500" />
                    New Transcription
                  </motion.button>
                </motion.div>
              </motion.div>
            )}

            {/* Failed State */}
            {status === 'failed' && (
              <motion.div 
                initial={{ opacity: 0, scale: 0.9 }} 
                animate={{ opacity: 1, scale: 1 }} 
                className="flex flex-col items-center py-16 space-y-6"
              >
                <motion.div 
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ type: "spring", stiffness: 200 }}
                  className="relative"
                >
                  <motion.div 
                    className="absolute inset-0 bg-red-500/30 rounded-full blur-2xl"
                    animate={{ 
                      scale: [1, 1.3, 1],
                      opacity: [0.3, 0.6, 0.3]
                    }}
                    transition={{ duration: 2, repeat: Infinity }}
                  />
                  <div className="relative w-24 h-24 rounded-full bg-gradient-to-br from-red-500/30 to-red-600/30 flex items-center justify-center border-2 border-red-400/50 shadow-2xl">
                    <XCircle className="w-12 h-12 text-red-300" strokeWidth={2.5} />
                  </div>
                </motion.div>
                <div className="text-center space-y-3 max-w-md">
                  <h3 className="text-3xl font-bold text-white">Transcription Failed</h3>
                  <p className="text-slate-300 text-lg">We encountered an issue processing your file. Please try again or contact support if the problem persists.</p>
                </div>
                <motion.button 
                  onClick={handleReset}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  className="px-10 py-4 bg-gradient-to-r from-slate-700 to-slate-800 hover:from-slate-600 hover:to-slate-700 text-white rounded-2xl font-semibold transition-all duration-300 border border-slate-600/50 shadow-xl flex items-center gap-3 mt-4 group"
                >
                  <RefreshCw className="w-5 h-5 group-hover:rotate-180 transition-transform duration-500" />
                  Try Again
                </motion.button>
              </motion.div>
            )}
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default TranscriptionModule;
