import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, Play, FileAudio, Copy, CheckCircle, XCircle, Loader2, FileText } from 'lucide-react';
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

  useEffect(() => {
    if (jobId && status === 'processing') {
      const interval = setInterval(async () => {
        try {
          const response = await fetch(`${API_URL}/status/${jobId}`, {
            headers: {
              ...getAuthHeader()
            }
          });
          const data = await response.json();
          
          setStatus(data.status);
          setStep(data.step || '');
          
          if (data.step) {
            setLiveLogs(prev => [...prev, `${data.step}`].slice(-4));
          }
          
          if (data.status === 'completed') {
            setTranscript(data.transcript);
            clearInterval(interval);
          } else if (data.status === 'failed') {
            clearInterval(interval);
          }
        } catch (error) {
          console.error('Error polling status:', error);
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
        {/* Info Cards at Top */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12"
        >
          <motion.div 
            className="relative overflow-hidden rounded-2xl p-6 border border-blue-500/30"
            style={{ background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.15) 0%, rgba(37, 99, 235, 0.25) 100%)' }}
            whileHover={{ scale: 1.05, y: -5 }}
            transition={{ type: "spring", stiffness: 300 }}
          >
            <motion.div 
              className="absolute inset-0 bg-gradient-to-br from-blue-400/20 to-transparent"
              animate={{ 
                backgroundPosition: ['0% 0%', '100% 100%'],
              }}
              transition={{ duration: 3, repeat: Infinity, repeatType: "reverse" }}
            />
            <div className="relative flex items-center gap-4 mb-3">
              <motion.div 
                className="w-14 h-14 rounded-xl bg-blue-500/30 flex items-center justify-center border border-blue-400/50 shadow-lg shadow-blue-500/30"
                animate={{ rotate: [0, 360] }}
                transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
              >
                <FileAudio className="w-7 h-7 text-blue-300" strokeWidth={2} />
              </motion.div>
              <h3 className="text-white font-bold text-lg">Multiple Formats</h3>
            </div>
            <p className="relative text-blue-100 text-sm leading-relaxed">Support for MP4, AVI, MOV, MP3, WAV, and M4A files</p>
          </motion.div>
          
          <motion.div 
            className="relative overflow-hidden rounded-2xl p-6 border border-emerald-500/30"
            style={{ background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(5, 150, 105, 0.25) 100%)' }}
            whileHover={{ scale: 1.05, y: -5 }}
            transition={{ type: "spring", stiffness: 300, delay: 0.1 }}
          >
            <motion.div 
              className="absolute inset-0 bg-gradient-to-br from-emerald-400/20 to-transparent"
              animate={{ 
                backgroundPosition: ['0% 0%', '100% 100%'],
              }}
              transition={{ duration: 3, repeat: Infinity, repeatType: "reverse", delay: 0.5 }}
            />
            <div className="relative flex items-center gap-4 mb-3">
              <motion.div 
                className="w-14 h-14 rounded-xl bg-emerald-500/30 flex items-center justify-center border border-emerald-400/50 shadow-lg shadow-emerald-500/30"
                animate={{ scale: [1, 1.1, 1] }}
                transition={{ duration: 2, repeat: Infinity }}
              >
                <CheckCircle className="w-7 h-7 text-emerald-300" strokeWidth={2} />
              </motion.div>
              <h3 className="text-white font-bold text-lg">High Accuracy</h3>
            </div>
            <p className="relative text-emerald-100 text-sm leading-relaxed">AI-powered Urdu transcription with 95%+ accuracy rate</p>
          </motion.div>
          
          <motion.div 
            className="relative overflow-hidden rounded-2xl p-6 border border-purple-500/30"
            style={{ background: 'linear-gradient(135deg, rgba(168, 85, 247, 0.15) 0%, rgba(126, 34, 206, 0.25) 100%)' }}
            whileHover={{ scale: 1.05, y: -5 }}
            transition={{ type: "spring", stiffness: 300, delay: 0.2 }}
          >
            <motion.div 
              className="absolute inset-0 bg-gradient-to-br from-purple-400/20 to-transparent"
              animate={{ 
                backgroundPosition: ['0% 0%', '100% 100%'],
              }}
              transition={{ duration: 3, repeat: Infinity, repeatType: "reverse", delay: 1 }}
            />
            <div className="relative flex items-center gap-4 mb-3">
              <motion.div 
                className="w-14 h-14 rounded-xl bg-purple-500/30 flex items-center justify-center border border-purple-400/50 shadow-lg shadow-purple-500/30"
                animate={{ rotate: [0, 360] }}
                transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
              >
                <Loader2 className="w-7 h-7 text-purple-300" strokeWidth={2} />
              </motion.div>
              <h3 className="text-white font-bold text-lg">Fast Processing</h3>
            </div>
            <p className="relative text-purple-100 text-sm leading-relaxed">Get your transcription in minutes, not hours</p>
          </motion.div>
        </motion.div>

        {/* Main Card */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="backdrop-blur-2xl bg-slate-900/40 rounded-3xl border border-slate-700/50 shadow-[0_20px_60px_rgba(0,0,0,0.6)] overflow-hidden"
        >
          
          {/* Header */}
          <div className="px-8 py-6 border-b border-slate-700/50">
            <h1 className="text-3xl font-bold text-white">Transcription Studio</h1>
            <p className="text-slate-400 mt-2">Transform your audio into text with AI precision</p>
          </div>

          {/* Main Content Area */}
          <div className="p-8">
            
            {/* Upload Section - Idle State */}
            {status === 'idle' && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
                <div
                  className={`relative rounded-2xl p-12 transition-all duration-300 overflow-hidden ${
                    isDragging ? 'scale-[1.02]' : ''
                  }`}
                  style={{
                    background: isDragging 
                      ? 'linear-gradient(135deg, rgba(59, 130, 246, 0.12) 0%, rgba(37, 99, 235, 0.08) 100%)'
                      : 'linear-gradient(135deg, rgba(30, 41, 59, 0.3) 0%, rgba(15, 23, 42, 0.5) 100%)',
                    border: isDragging ? '2px solid rgba(59, 130, 246, 0.4)' : '2px solid rgba(100, 116, 139, 0.2)',
                  }}
                  onDrop={handleDrop}
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                >
                  <input ref={fileInputRef} type="file" accept="video/*,audio/*" onChange={handleFileSelect} className="hidden" />
                  
                  <div className="relative flex flex-col items-center gap-6">
                    <motion.div
                      animate={{ 
                        y: isDragging ? [0, -8, 0] : 0,
                        scale: isDragging ? 1.1 : 1
                      }}
                      transition={{ duration: 0.6, repeat: isDragging ? Infinity : 0 }}
                      className="relative"
                    >
                      <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-blue-500/20 to-blue-600/20 flex items-center justify-center border border-blue-500/30 shadow-lg shadow-blue-500/10">
                        <Upload className="w-9 h-9 text-blue-300" strokeWidth={1.5} />
                      </div>
                    </motion.div>

                    <div className="text-center space-y-2">
                      <h3 className="text-2xl text-white font-semibold">
                        {isDragging ? 'Drop your file here' : 'Upload Your Media'}
                      </h3>
                      <p className="text-slate-400">
                        Drag and drop or click to browse
                      </p>
                    </div>

                    <button 
                      onClick={handleUploadClick} 
                      className="px-8 py-3 bg-gradient-to-r from-slate-700 to-slate-800 hover:from-slate-600 hover:to-slate-700 text-white rounded-full font-medium transition-all duration-300 border border-slate-600/50 shadow-lg hover:shadow-slate-700/50 flex items-center gap-2"
                    >
                      <FileAudio className="w-4 h-4" />
                      Browse Files
                    </button>
                  </div>
                </div>

                <AnimatePresence>
                  {file && (
                    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }} transition={{ duration: 0.4 }}>
                      <div className="flex items-center justify-between bg-gradient-to-r from-slate-800/50 to-slate-900/50 rounded-xl p-6 border border-slate-700/50 shadow-lg backdrop-blur-sm">
                        <div className="flex items-center gap-4">
                          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500/20 to-blue-600/20 flex items-center justify-center border border-blue-500/30">
                            <FileAudio className="w-6 h-6 text-blue-300" strokeWidth={1.5} />
                          </div>
                          <div>
                            <p className="text-white font-semibold">{file.name}</p>
                            <p className="text-slate-400 text-sm">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                          </div>
                        </div>
                        <button onClick={handleStartTranscription} className="px-8 py-3 bg-gradient-to-r from-white to-slate-100 hover:from-slate-50 hover:to-slate-200 text-slate-900 font-semibold rounded-full transition-all duration-300 shadow-lg shadow-slate-300/50 flex items-center gap-2 border border-slate-200">
                          <Play className="w-4 h-4 fill-slate-900" />
                          Start
                        </button>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            )}

            {/* Processing State */}
            {status === 'processing' && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex flex-col items-center py-12 space-y-6">
                <div className="relative">
                  <motion.div animate={{ rotate: 360 }} transition={{ duration: 2, repeat: Infinity, ease: 'linear' }} className="w-20 h-20 rounded-full border-4 border-slate-700 border-t-blue-500" />
                  <div className="absolute inset-0 flex items-center justify-center">
                    <Loader2 className="w-8 h-8 text-blue-500" />
                  </div>
                </div>
                
                <div className="text-center space-y-2">
                  <h3 className="text-2xl font-semibold text-white">Processing</h3>
                  <p className="text-slate-400">{step || 'Initializing transcription...'}</p>
                </div>

                {liveLogs.length > 0 && (
                  <div className="w-full max-w-2xl bg-slate-950/50 rounded-xl p-4 border border-slate-700/50">
                    <div className="space-y-2 font-mono text-sm">
                      {liveLogs.map((log, idx) => (
                        <motion.div key={idx} initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} className="text-blue-400">
                          → {log}
                        </motion.div>
                      ))}
                    </div>
                  </div>
                )}
              </motion.div>
            )}

            {/* Completed State */}
            {status === 'completed' && (
              <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="space-y-6">
                <div className="flex items-center gap-3 justify-center">
                  <div className="w-12 h-12 rounded-full bg-green-500/20 flex items-center justify-center">
                    <CheckCircle className="w-7 h-7 text-green-400" />
                  </div>
                  <h3 className="text-2xl font-semibold text-white">Complete</h3>
                </div>

                <div className="bg-slate-950/50 rounded-xl border border-slate-700/50 overflow-hidden">
                  <div className="flex items-center justify-between px-6 py-4 border-b border-slate-700/50">
                    <div className="flex items-center gap-2 text-white font-medium">
                      <FileText className="w-5 h-5" />
                      Transcript
                    </div>
                    <button onClick={copyToClipboard} className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg transition-colors text-sm">
                      {copied ? (
                        <>
                          <CheckCircle className="w-4 h-4 text-green-400" />
                          Copied
                        </>
                      ) : (
                        <>
                          <Copy className="w-4 h-4" />
                          Copy
                        </>
                      )}
                    </button>
                  </div>
                  <div className="p-6 text-slate-200 whitespace-pre-wrap max-h-96 overflow-y-auto custom-scrollbar leading-relaxed">
                    {transcript}
                  </div>
                </div>

                <div className="flex justify-center">
                  <button onClick={handleReset} className="px-8 py-3 bg-slate-800 hover:bg-slate-700 text-white rounded-full font-medium transition-colors border border-slate-600">
                    New Transcription
                  </button>
                </div>
              </motion.div>
            )}

            {/* Failed State */}
            {status === 'failed' && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex flex-col items-center py-12 space-y-4">
                <div className="w-16 h-16 rounded-full bg-red-500/20 flex items-center justify-center">
                  <XCircle className="w-10 h-10 text-red-400" />
                </div>
                <div className="text-center space-y-2">
                  <h3 className="text-2xl font-semibold text-white">Failed</h3>
                  <p className="text-slate-400">Something went wrong. Please try again.</p>
                </div>
                <button onClick={handleReset} className="px-8 py-3 bg-slate-800 hover:bg-slate-700 text-white rounded-full font-medium transition-colors border border-slate-600 mt-4">
                  Try Again
                </button>
              </motion.div>
            )}
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default TranscriptionModule;
