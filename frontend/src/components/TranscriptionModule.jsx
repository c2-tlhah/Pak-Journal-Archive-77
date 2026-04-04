import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, Play, FileAudio, Copy, CheckCircle, XCircle, Loader2, FileText, Download, RefreshCw, Sparkles, Zap, Clock, Globe } from 'lucide-react';
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
    <div className="relative min-h-screen overflow-hidden pt-24 pb-12 px-4 flex flex-col items-center justify-center">
      <GoldenBackground variant="transcription" />
      
      <div className="relative z-10 w-full max-w-3xl mx-auto">
        {/* Hero Section - Minimalist */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="text-center mb-8"
        >
          <h1 className="text-4xl font-bold text-slate-900 mb-2 tracking-tight drop-shadow-sm">
            Transcription Studio
          </h1>
        </motion.div>
        
        {/* Main Card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="relative bg-white/20 backdrop-blur-3xl rounded-3xl shadow-2xl overflow-hidden border border-white/30"
        >
          
          {/* Main Content Area */}
          <div className="relative p-6 md:p-8">
            
            {/* Upload Section - Idle State */}
            {status === 'idle' && (
              <motion.div 
                initial={{ opacity: 0, scale: 0.98 }} 
                animate={{ opacity: 1, scale: 1 }} 
                transition={{ duration: 0.4 }}
                className="w-full space-y-6"
              >
                <div
                  className={`relative w-full h-64 rounded-2xl transition-all duration-300 overflow-hidden cursor-pointer group flex flex-col items-center justify-center ${
                    isDragging 
                      ? 'bg-amber-500/5' 
                      : 'bg-transparent hover:bg-white/10'
                  }`}
                  onDrop={handleDrop}
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onClick={handleUploadClick}
                >
                  <input ref={fileInputRef} type="file" accept="video/*" onChange={handleFileSelect} className="hidden" />
                  
                  <div className="flex flex-col items-center gap-6 p-6">
                    
                    <div className="text-center space-y-1">
                        <p className="text-lg font-medium text-slate-800">Drag & drop or click to upload</p>
                        <p className="text-xs text-slate-600 font-medium tracking-wide uppercase">Supports Video Files Only</p>
                    </div>

                    <button className="mt-2 px-8 py-3 bg-slate-900 text-white rounded-full font-bold text-sm hover:bg-black transition-all shadow-lg hover:shadow-slate-900/20 transform hover:-translate-y-0.5 active:translate-y-0 flex items-center gap-2 backdrop-blur-md">
                        <Upload className="w-4 h-4" strokeWidth={2.5} />
                        Browse Files
                    </button>
                  </div>
                </div>

                <AnimatePresence>
                  {file && (
                    <motion.div 
                      initial={{ opacity: 0, y: 30, scale: 0.9 }} 
                      animate={{ opacity: 1, y: 0, scale: 1 }} 
                      exit={{ opacity: 0, y: -20, scale: 0.9 }} 
                      transition={{ type: "spring", stiffness: 200, damping: 20 }}
                    >
                      <div className="relative overflow-hidden flex flex-col md:flex-row items-center justify-between bg-gradient-to-r from-slate-800/70 via-slate-800/60 to-slate-900/70 rounded-2xl p-6 shadow-2xl backdrop-blur-xl gap-6">
                        <motion.div 
                          className="absolute inset-0 bg-gradient-to-r from-amber-500/10 to-slate-500/10"
                          animate={{ 
                            x: ['0%', '100%', '0%'],
                          }}
                          transition={{ duration: 3, repeat: Infinity }}
                        />
                        <div className="relative flex items-center gap-5 flex-1">
                          <motion.div 
                            className="w-14 h-14 rounded-2xl bg-gradient-to-br from-amber-500/30 to-amber-700/30 flex items-center justify-center shadow-xl shadow-amber-500/20"
                            animate={{ rotate: [0, 5, -5, 0] }}
                            transition={{ duration: 2, repeat: Infinity }}
                          >
                            <FileAudio className="w-7 h-7 text-amber-200" strokeWidth={2} />
                          </motion.div>
                          <div className="flex-1">
                            <p className="text-white font-bold text-lg mb-1">{file.name}</p>
                            <div className="flex items-center gap-3 text-sm text-slate-300">
                              <span className="flex items-center gap-1">
                                <FileText className="w-4 h-4" />
                                {(file.size / 1024 / 1024).toFixed(2)} MB
                              </span>
                              <span className="text-slate-500">•</span>
                              <span className="px-2 py-0.5 rounded-md bg-amber-500/20 text-amber-300 text-xs font-medium">
                                Ready
                              </span>
                            </div>
                          </div>
                        </div>
                        <motion.button 
                          onClick={handleStartTranscription}
                          whileHover={{ scale: 1.05 }}
                          whileTap={{ scale: 0.95 }}
                          className="relative px-8 py-3 bg-white text-black font-bold rounded-xl transition-all duration-300 shadow-lg flex items-center gap-2 group overflow-hidden"
                        >
                          <Play className="relative w-4 h-4 fill-black group-hover:scale-110 transition-transform" />
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
                    className="w-32 h-32 rounded-full border-4 border-slate-700/50 border-t-amber-400 border-r-amber-600"
                  />
                  <motion.div 
                    animate={{ rotate: -360 }} 
                    transition={{ duration: 3, repeat: Infinity, ease: 'linear' }} 
                    className="absolute inset-2 rounded-full border-4 border-slate-700/30 border-b-amber-300"
                  />
                  <motion.div 
                    className="absolute inset-0 flex items-center justify-center"
                    animate={{ scale: [1, 1.1, 1] }}
                    transition={{ duration: 2, repeat: Infinity }}
                  >
                    <div className="w-16 h-16 rounded-full bg-gradient-to-br from-amber-500/30 to-amber-700/30 flex items-center justify-center">
                      <Globe className="w-8 h-8 text-amber-200" />
                    </div>
                  </motion.div>
                  <motion.div 
                    className="absolute -inset-4 bg-amber-500/20 rounded-full blur-2xl"
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
                      className="w-2 h-2 rounded-full bg-amber-400"
                      animate={{ scale: [1, 1.5, 1], opacity: [0.5, 1, 0.5] }}
                      transition={{ duration: 1, repeat: Infinity, delay: 0 }}
                    />
                    <motion.div 
                      className="w-2 h-2 rounded-full bg-amber-500"
                      animate={{ scale: [1, 1.5, 1], opacity: [0.5, 1, 0.5] }}
                      transition={{ duration: 1, repeat: Infinity, delay: 0.2 }}
                    />
                    <motion.div 
                      className="w-2 h-2 rounded-full bg-amber-600"
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
                      <div className="w-3 h-3 rounded-full bg-amber-400 animate-pulse" />
                      <span className="text-slate-300 font-semibold text-sm">Live Progress</span>
                    </div>
                    <div className="space-y-3 font-mono text-sm">
                      {liveLogs.map((log, idx) => (
                        <motion.div 
                          key={idx} 
                          initial={{ opacity: 0, x: -20 }} 
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: idx * 0.1 }}
                          className="flex items-start gap-3 text-amber-200 bg-slate-900/50 rounded-lg px-4 py-3 border border-slate-700/30"
                        >
                          <Zap className="w-4 h-4 mt-0.5 flex-shrink-0 text-amber-400" />
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
                    className="relative w-20 h-20 rounded-full bg-gradient-to-br from-amber-500/30 to-amber-700/30 flex items-center justify-center border-2 border-amber-400/50 shadow-2xl shadow-amber-500/30"
                    animate={{ 
                      boxShadow: [
                        '0 0 20px rgba(245, 158, 11, 0.3)',
                        '0 0 40px rgba(245, 158, 11, 0.5)',
                        '0 0 20px rgba(245, 158, 11, 0.3)'
                      ]
                    }}
                    transition={{ duration: 2, repeat: Infinity }}
                  >
                    <CheckCircle className="w-10 h-10 text-amber-300" strokeWidth={2.5} />
                  </motion.div>
                  <div className="text-center">
                    <h3 className="text-3xl font-bold text-white mb-2">Transcription Complete!</h3>
                    <p className="text-slate-300">Your transcript is ready to download or copy</p>
                  </div>
                </motion.div>

                <motion.div 
                  initial={{ y: 20, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  transition={{ delay: 0.3 }}
                  className="relative bg-slate-950/60 rounded-2xl border border-slate-600/50 overflow-hidden backdrop-blur-xl shadow-2xl"
                >
                  <div className="absolute inset-0 bg-gradient-to-br from-amber-500/5 to-slate-500/5" />
                  
                  <div className="relative flex flex-wrap items-center justify-between px-8 py-5 border-b border-slate-600/50 bg-slate-900/50 gap-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500/30 to-amber-700/30 flex items-center justify-center border border-amber-400/30">
                        <FileText className="w-5 h-5 text-amber-200" />
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
                            <CheckCircle className="w-4 h-4 text-amber-400" />
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
                        className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-amber-600 to-amber-700 hover:from-amber-500 hover:to-amber-600 text-white rounded-xl transition-all duration-300 text-sm font-medium border border-amber-400/30 shadow-xl shadow-amber-500/30"
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
