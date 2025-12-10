import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { FiVideo, FiClock, FiCalendar, FiDownload, FiEye, FiFileText, FiPlay, FiTrash2, FiEdit2, FiCheck, FiX, FiMoreVertical, FiSearch, FiFilter } from 'react-icons/fi';
import GoldenBackground from '../components/GoldenBackground';

const API_BASE_URL = import.meta.env.PROD 
  ? 'https://pak-journal-archive-77.onrender.com'
  : 'http://localhost:5000';

function Library() {
  const { user, getAuthHeader, isAuthenticated, loading: authLoading } = useAuth();
  const navigate = useNavigate();
  const [videos, setVideos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedVideo, setSelectedVideo] = useState(null);
  const [mediaModal, setMediaModal] = useState(false);
  const [activeTab, setActiveTab] = useState('video'); // 'video' or 'transcript'
  const [fullTranscript, setFullTranscript] = useState(null);
  const [editingVideoId, setEditingVideoId] = useState(null);
  const [editTitle, setEditTitle] = useState('');
  const [activeMenuId, setActiveMenuId] = useState(null);
  const [editingSpeakerId, setEditingSpeakerId] = useState(null);
  const [editSpeakerName, setEditSpeakerName] = useState('');

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (activeMenuId && !event.target.closest('.video-menu-trigger') && !event.target.closest('.video-menu-dropdown')) {
        setActiveMenuId(null);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [activeMenuId]);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      navigate('/login');
      return;
    }
    
    if (isAuthenticated) {
      fetchVideos();
    }
  }, [isAuthenticated, authLoading, navigate]);

  const formatTime = (seconds) => {
    const date = new Date(0);
    date.setSeconds(seconds);
    const hh = date.getUTCHours();
    const mm = date.getUTCMinutes();
    const ss = date.getUTCSeconds().toString().padStart(2, '0');
    if (hh) {
      return `${hh}:${mm.toString().padStart(2, '0')}:${ss}`;
    }
    return `${mm}:${ss}`;
  };

  const deleteVideo = async (videoId, e) => {
    e.stopPropagation();
    if (!window.confirm('Are you sure you want to delete this video? This action cannot be undone.')) {
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/videos/${videoId}`, {
        method: 'DELETE',
        headers: getAuthHeader()
      });

      if (response.ok) {
        setVideos(videos.filter(v => v.id !== videoId));
        if (selectedVideo && selectedVideo.id === videoId) {
          setMediaModal(false);
          setSelectedVideo(null);
        }
      } else {
        console.error('Failed to delete video');
        alert('Failed to delete video');
      }
    } catch (error) {
      console.error('Error deleting video:', error);
      alert('Error deleting video');
    }
  };

  const startEditing = (video, e) => {
    e.stopPropagation();
    setEditingVideoId(video.id);
    setEditTitle(video.original_filename || video.filename || 'Untitled Video');
  };

  const cancelEditing = (e) => {
    if (e) e.stopPropagation();
    setEditingVideoId(null);
    setEditTitle('');
  };

  const saveTitle = async (videoId, e) => {
    e.stopPropagation();
    
    if (!editTitle.trim()) {
      alert('Title cannot be empty');
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/videos/${videoId}/rename`, {
        method: 'PUT',
        headers: {
          ...getAuthHeader(),
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ title: editTitle.trim() })
      });

      if (response.ok) {
        setVideos(videos.map(v => 
          v.id === videoId ? { ...v, original_filename: editTitle.trim() } : v
        ));
        if (selectedVideo && selectedVideo.id === videoId) {
          setSelectedVideo({ ...selectedVideo, original_filename: editTitle.trim() });
        }
        setEditingVideoId(null);
        setEditTitle('');
      } else {
        const error = await response.json();
        alert(error.error || 'Failed to rename video');
      }
    } catch (error) {
      console.error('Error renaming video:', error);
      alert('Error renaming video');
    }
  };

  const startEditingSpeaker = (video, e) => {
    e.stopPropagation();
    setEditingSpeakerId(video.id);
    setEditSpeakerName(video.speaker || 'Unknown Speaker');
  };

  const cancelEditingSpeaker = (e) => {
    if (e) e.stopPropagation();
    setEditingSpeakerId(null);
    setEditSpeakerName('');
  };

  const saveSpeaker = async (videoId, e) => {
    e.stopPropagation();
    
    if (!editSpeakerName.trim()) {
      alert('Speaker name cannot be empty');
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/videos/${videoId}/speaker`, {
        method: 'PUT',
        headers: {
          ...getAuthHeader(),
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ speaker: editSpeakerName.trim() })
      });

      if (response.ok) {
        setVideos(videos.map(v => 
          v.id === videoId ? { ...v, speaker: editSpeakerName.trim() } : v
        ));
        if (selectedVideo && selectedVideo.id === videoId) {
          setSelectedVideo({ ...selectedVideo, speaker: editSpeakerName.trim() });
        }
        setEditingSpeakerId(null);
        setEditSpeakerName('');
      } else {
        const error = await response.json();
        alert(error.error || 'Failed to update speaker');
      }
    } catch (error) {
      console.error('Error updating speaker:', error);
      alert('Error updating speaker');
    }
  };

  const fetchVideos = async () => {
    try {
      setLoading(true);
      setError(null);

      console.log('Fetching videos from:', `${API_BASE_URL}/api/videos`);
      
      const response = await fetch(`${API_BASE_URL}/api/videos`, {
        method: 'GET',
        headers: {
          ...getAuthHeader(),
          'Content-Type': 'application/json'
        }
      });

      console.log('Response status:', response.status);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
        throw new Error(errorData.error || `Server error: ${response.status}`);
      }

      const data = await response.json();
      console.log('Received data:', data);
      setVideos(data.videos || []);
      setError(null);
    } catch (err) {
      console.error('Error fetching videos:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const openMediaModal = async (video, tab = 'video') => {
    setSelectedVideo(video);
    setActiveTab(tab);
    setMediaModal(true);
    
    if (video.has_transcription) {
      try {
        const response = await fetch(`${API_BASE_URL}/api/videos/${video.id}/transcript`, {
          headers: {
            ...getAuthHeader()
          }
        });

        if (response.ok) {
          const data = await response.json();
          setFullTranscript(data.transcription);
        }
      } catch (err) {
        console.error('Error fetching transcript:', err);
      }
    } else {
      setFullTranscript(null);
    }
  };

  const downloadTranscript = (transcript, filename) => {
    const blob = new Blob([transcript], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${filename}_transcript.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const formatDuration = (seconds) => {
    if (!seconds) return 'N/A';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (authLoading || loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-amber-500 mx-auto"></div>
          <p className="text-slate-600 mt-6 text-lg font-medium tracking-wide">Loading your archive...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null; // Will redirect to login
  }

  return (
    <div className="relative min-h-screen w-full overflow-hidden text-slate-900 font-sans selection:bg-amber-300">
      <GoldenBackground variant="library" />
      
      <div className="relative z-10 max-w-7xl mx-auto px-6 py-24">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className="text-center mb-16"
        >
          <h1 className="text-5xl md:text-7xl font-medium tracking-tight text-slate-900 mb-6 drop-shadow-sm">
            Video Archive
          </h1>
          <p className="text-lg md:text-xl text-slate-700 max-w-2xl mx-auto leading-relaxed font-light">
            Browse and manage your transcribed archives with precision and ease.
          </p>
          <div className="mt-6 inline-flex items-center px-4 py-2 rounded-full bg-white/30 backdrop-blur-md border border-white/40 shadow-sm">
            <span className="font-semibold text-slate-900 mr-2">{videos.length}</span> 
            <span className="text-slate-700">videos archived</span>
          </div>
        </motion.div>

        {/* Error Message */}
        {error && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-red-50 border border-red-200 text-red-700 px-6 py-4 rounded-xl mb-12 text-center shadow-sm max-w-2xl mx-auto"
          >
            <p className="mb-4 font-medium">{error}</p>
            <button
              onClick={fetchVideos}
              className="bg-red-600 hover:bg-red-700 text-white px-6 py-2 rounded-lg font-semibold transition-all duration-300 shadow-md hover:shadow-lg"
            >
              Retry Connection
            </button>
          </motion.div>
        )}

        {/* Videos Grid */}
        {videos.length === 0 ? (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center py-32 bg-white/20 backdrop-blur-md rounded-3xl border border-white/30 shadow-xl"
          >
            <div className="bg-white/40 w-24 h-24 rounded-full flex items-center justify-center mx-auto mb-6 shadow-inner">
                <FiVideo className="w-10 h-10 text-slate-600" />
            </div>
            <h3 className="text-3xl font-medium text-slate-800 mb-4">No videos archived yet</h3>
            <p className="text-slate-600 mb-10 max-w-md mx-auto">Start building your archive by uploading and transcribing your first video content.</p>
            <a
              href="/transcribe"
              className="inline-flex items-center bg-slate-900 text-white px-8 py-4 rounded-full font-bold tracking-wide hover:bg-slate-800 transition-all duration-300 shadow-xl hover:scale-105 hover:shadow-2xl"
            >
              <FiPlay className="mr-2 w-5 h-5" />
              Start Transcribing
            </a>
          </motion.div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            <AnimatePresence>
            {videos.map((video, index) => (
              <motion.div
                key={video.id}
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.9 }}
                transition={{ duration: 0.5, delay: index * 0.05 }}
                className="bg-white/40 backdrop-blur-md border border-white/50 rounded-2xl overflow-hidden hover:border-white/80 transition-all duration-500 hover:shadow-2xl hover:shadow-amber-900/10 group cursor-pointer relative flex flex-col"
                onClick={() => openMediaModal(video)}
              >
                {/* Video Thumbnail/Icon */}
                <div className="relative aspect-video bg-slate-900 flex items-center justify-center overflow-hidden rounded-t-2xl group-hover:shadow-inner transition-all duration-500">
                  {video.video_url ? (
                    <video 
                      src={`${API_BASE_URL}${video.video_url}`}
                      className="w-full h-full object-cover opacity-90 group-hover:opacity-100 group-hover:scale-105 transition-all duration-700"
                      muted
                      loop
                      onMouseOver={e => e.target.play().catch(() => {})}
                      onMouseOut={e => {
                        e.target.pause();
                        e.target.currentTime = 0;
                      }}
                    />
                  ) : (
                    <div className="w-full h-full bg-gradient-to-br from-slate-800 to-slate-900 flex items-center justify-center">
                      <FiVideo className="w-16 h-16 text-slate-600" />
                    </div>
                  )}
                  
                  {/* Play Overlay */}
                  <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all duration-300 bg-black/20 backdrop-blur-[2px]">
                    <div className="bg-white/90 p-4 rounded-full shadow-2xl transform scale-75 group-hover:scale-100 transition-all duration-300">
                      <FiPlay className="w-6 h-6 text-slate-900 fill-current ml-1" />
                    </div>
                  </div>

                  {/* Status Badges */}
                  <div className="absolute top-3 right-3 flex gap-2">
                    {video.status === 'completed' && (
                      <div className="bg-emerald-500/90 backdrop-blur-md text-white text-[10px] uppercase tracking-wider px-2.5 py-1 rounded-full font-bold shadow-sm">
                        Ready
                      </div>
                    )}
                    {video.status === 'processing' && (
                      <div className="bg-amber-500/90 backdrop-blur-md text-white text-[10px] uppercase tracking-wider px-2.5 py-1 rounded-full font-bold shadow-sm animate-pulse">
                        Processing
                      </div>
                    )}
                    {video.has_transcription && (
                      <div className="bg-slate-900/80 backdrop-blur-md text-white text-[10px] uppercase tracking-wider px-2.5 py-1 rounded-full font-bold shadow-sm flex items-center gap-1">
                        <FiFileText className="w-3 h-3" />
                        Text
                      </div>
                    )}
                  </div>
                  
                  {/* Duration Badge */}
                  <div className="absolute bottom-3 right-3 bg-black/60 backdrop-blur-md text-white text-xs px-2 py-1 rounded-md font-mono border border-white/10">
                    {formatDuration(video.duration)}
                  </div>
                </div>

                {/* Video Info */}
                <div className="p-6 flex-1 flex flex-col">
                  <div className="flex justify-between items-start mb-4 relative">
                    {/* Editable Title */}
                    {editingVideoId === video.id ? (
                      <div className="flex-1 flex items-center gap-2 mr-2" onClick={(e) => e.stopPropagation()}>
                        <input
                          type="text"
                          value={editTitle}
                          onChange={(e) => setEditTitle(e.target.value)}
                          className="w-full bg-white/80 text-slate-900 px-3 py-2 rounded-lg border border-amber-400 focus:ring-2 focus:ring-amber-400/50 outline-none text-base font-medium shadow-inner font-urdu"
                          autoFocus
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') saveTitle(video.id, e);
                            if (e.key === 'Escape') cancelEditing(e);
                          }}
                        />
                        <button onClick={(e) => saveTitle(video.id, e)} className="bg-emerald-500 text-white p-2 rounded-lg hover:bg-emerald-600 shadow-md"><FiCheck /></button>
                        <button onClick={cancelEditing} className="bg-red-500 text-white p-2 rounded-lg hover:bg-red-600 shadow-md"><FiX /></button>
                      </div>
                    ) : (
                      <h3 className="text-lg font-bold text-slate-900 truncate flex-1 pr-4 leading-tight group-hover:text-amber-700 transition-colors font-urdu" title={video.original_filename || video.filename}>
                        {video.original_filename || video.filename || 'Untitled Video'}
                      </h3>
                    )}

                    {/* Options Menu */}
                    <div className="relative">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setActiveMenuId(activeMenuId === video.id ? null : video.id);
                        }}
                        className="video-menu-trigger text-slate-400 hover:text-slate-900 p-2 rounded-full hover:bg-slate-200/50 transition-all"
                      >
                        <FiMoreVertical className="w-5 h-5" />
                      </button>

                      {activeMenuId === video.id && (
                        <div className="video-menu-dropdown absolute right-0 top-10 w-56 bg-white/90 backdrop-blur-xl border border-white/50 rounded-xl shadow-2xl z-20 overflow-hidden py-2 animate-in fade-in zoom-in-95 duration-200 ring-1 ring-black/5">
                          {video.has_transcription && (
                            <>
                              <button
                                onClick={(e) => { e.stopPropagation(); openMediaModal(video, 'transcript'); setActiveMenuId(null); }}
                                className="w-full text-left px-5 py-3 text-sm text-slate-700 hover:bg-amber-50 hover:text-amber-900 flex items-center gap-3 transition-colors font-medium"
                              >
                                <FiEye className="w-4 h-4" /> View Transcript
                              </button>
                              <button
                                onClick={(e) => { 
                                  e.stopPropagation(); 
                                  if (fullTranscript && fullTranscript.transcript_text) {
                                    downloadTranscript(fullTranscript.transcript_text, video.filename);
                                  } else {
                                    openMediaModal(video, 'transcript');
                                  }
                                  setActiveMenuId(null); 
                                }}
                                className="w-full text-left px-5 py-3 text-sm text-slate-700 hover:bg-amber-50 hover:text-amber-900 flex items-center gap-3 transition-colors font-medium"
                              >
                                <FiDownload className="w-4 h-4" /> Download Text
                              </button>
                            </>
                          )}
                          <button
                            onClick={(e) => { startEditing(video, e); setActiveMenuId(null); }}
                            className="w-full text-left px-5 py-3 text-sm text-slate-700 hover:bg-amber-50 hover:text-amber-900 flex items-center gap-3 transition-colors font-medium"
                          >
                            <FiEdit2 className="w-4 h-4" /> Rename
                          </button>
                          <div className="h-px bg-slate-200 my-1 mx-4"></div>
                          <button
                            onClick={(e) => { deleteVideo(video.id, e); setActiveMenuId(null); }}
                            className="w-full text-left px-5 py-3 text-sm text-red-600 hover:bg-red-50 hover:text-red-700 flex items-center gap-3 transition-colors font-medium"
                          >
                            <FiTrash2 className="w-4 h-4" /> Delete
                          </button>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Speaker Info */}
                  <div className="mb-3 flex items-center gap-2">
                      <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Speaker:</span>
                      {editingSpeakerId === video.id ? (
                          <div className="flex-1 flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
                              <input
                                  type="text"
                                  value={editSpeakerName}
                                  onChange={(e) => setEditSpeakerName(e.target.value)}
                                  className="w-full bg-white/80 text-slate-900 px-2 py-1 rounded border border-amber-400 focus:ring-1 focus:ring-amber-400 outline-none text-sm"
                                  autoFocus
                                  onKeyDown={(e) => {
                                      if (e.key === 'Enter') saveSpeaker(video.id, e);
                                      if (e.key === 'Escape') cancelEditingSpeaker(e);
                                  }}
                              />
                              <button onClick={(e) => saveSpeaker(video.id, e)} className="text-emerald-600 hover:bg-emerald-50 p-1 rounded"><FiCheck size={14} /></button>
                              <button onClick={cancelEditingSpeaker} className="text-red-500 hover:bg-red-50 p-1 rounded"><FiX size={14} /></button>
                          </div>
                      ) : (
                          <div className="flex items-center gap-2 group/speaker cursor-pointer" onClick={(e) => startEditingSpeaker(video, e)}>
                              <span className={`text-sm font-medium ${video.speaker === 'Unknown Speaker' ? 'text-amber-600 italic' : 'text-slate-700'}`}>
                                  {video.speaker || 'Unknown Speaker'}
                              </span>
                              <FiEdit2 className="w-3 h-3 text-slate-300 opacity-0 group-hover/speaker:opacity-100 transition-opacity" />
                          </div>
                      )}
                  </div>

                  {/* Metadata */}
                  <div className="flex items-center gap-4 text-xs font-medium text-slate-500 mb-5">
                    <div className="flex items-center bg-white/40 px-2 py-1 rounded-md border border-white/30">
                      <FiCalendar className="w-3 h-3 mr-1.5 text-slate-400" />
                      <span>{formatDate(video.upload_date).split(',')[0]}</span>
                    </div>
                    <div className="flex items-center bg-white/40 px-2 py-1 rounded-md border border-white/30">
                      <FiFileText className="w-3 h-3 mr-1.5 text-slate-400" />
                      <span>{formatFileSize(video.file_size)}</span>
                    </div>
                  </div>

                  {/* Transcript Preview (Compact) */}
                  {video.has_transcription && video.transcript_preview ? (
                    <div className="bg-white/30 rounded-xl p-4 mt-auto border border-white/40 group-hover:bg-white/50 transition-colors relative overflow-hidden">
                      <p className="text-slate-600 text-xs leading-relaxed line-clamp-3 font-urdu" dir="auto">
                        "{video.transcript_preview}"
                      </p>
                    </div>
                  ) : (
                    <div className="mt-auto h-20 flex items-center justify-center bg-slate-100/50 rounded-xl border border-dashed border-slate-300">
                      <span className="text-xs text-slate-400 font-medium">No preview available</span>
                    </div>
                  )}
                </div>
              </motion.div>
            ))}
            </AnimatePresence>
          </div>
        )}
      </div>

      {/* Media Modal */}
      <AnimatePresence>
      {mediaModal && selectedVideo && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-slate-900/80 backdrop-blur-sm z-50 flex items-center justify-center p-4 md:p-8"
          onClick={() => setMediaModal(false)}
        >
          <motion.div
            initial={{ scale: 0.95, opacity: 0, y: 20 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.95, opacity: 0, y: 20 }}
            className="bg-white rounded-3xl max-w-6xl w-full h-[85vh] overflow-hidden shadow-2xl flex flex-col ring-1 ring-white/20"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="bg-slate-50 p-5 border-b border-slate-200 flex justify-between items-center">
              {editingVideoId === selectedVideo.id ? (
                <div className="flex items-center gap-2 flex-1 mr-4">
                  <input
                    type="text"
                    value={editTitle}
                    onChange={(e) => setEditTitle(e.target.value)}
                    className="flex-1 bg-white text-slate-900 px-4 py-2 rounded-lg border border-amber-400 focus:ring-2 focus:ring-amber-400/50 outline-none shadow-inner"
                    autoFocus
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') saveTitle(selectedVideo.id, e);
                      if (e.key === 'Escape') cancelEditing(e);
                    }}
                  />
                  <button onClick={(e) => saveTitle(selectedVideo.id, e)} className="bg-emerald-500 text-white p-2 rounded-lg hover:bg-emerald-600 shadow-sm"><FiCheck /></button>
                  <button onClick={cancelEditing} className="bg-red-500 text-white p-2 rounded-lg hover:bg-red-600 shadow-sm"><FiX /></button>
                </div>
              ) : (
                <div className="flex items-center gap-3 flex-1 overflow-hidden">
                  <h2 className="text-xl md:text-2xl font-bold text-slate-900 truncate max-w-2xl">
                    {selectedVideo.original_filename || selectedVideo.filename || 'Untitled Video'}
                  </h2>
                  <button
                    onClick={(e) => startEditing(selectedVideo, e)}
                    className="text-slate-400 hover:text-amber-600 transition-colors p-1 rounded-full hover:bg-amber-50"
                    title="Rename"
                  >
                    <FiEdit2 className="w-4 h-4" />
                  </button>
                </div>
              )}
              <div className="flex gap-3 items-center">
                <button
                  onClick={(e) => deleteVideo(selectedVideo.id, e)}
                  className="text-red-400 hover:text-red-600 transition-colors p-2 rounded-full hover:bg-red-50"
                  title="Delete Video"
                >
                  <FiTrash2 className="w-5 h-5" />
                </button>
                <button
                  onClick={() => setMediaModal(false)}
                  className="bg-slate-100 hover:bg-slate-200 text-slate-500 hover:text-slate-900 transition-colors rounded-full w-10 h-10 flex items-center justify-center"
                >
                  <FiX className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Modal Content */}
            <div className="flex-1 flex flex-col md:flex-row overflow-hidden bg-slate-50">
              {/* Video Player Section */}
              <div className={`flex-1 bg-black flex items-center justify-center relative ${activeTab === 'transcript' ? 'hidden md:flex' : ''}`}>
                {selectedVideo.video_url ? (
                  <video 
                    src={`${API_BASE_URL}${selectedVideo.video_url}`}
                    className="w-full h-full max-h-[calc(85vh-80px)] object-contain"
                    controls
                    autoPlay={activeTab === 'video'}
                  />
                ) : (
                  <div className="text-gray-500 flex flex-col items-center">
                    <FiVideo className="w-16 h-16 mb-4" />
                    <p>Video source not available</p>
                  </div>
                )}
              </div>

              {/* Transcript Section */}
              <div className={`w-full md:w-[450px] lg:w-[550px] bg-white border-l border-slate-200 flex flex-col shadow-xl z-10 ${activeTab === 'video' ? 'hidden md:flex' : ''}`}>
                {/* Tabs for Mobile */}
                <div className="flex md:hidden border-b border-slate-200">
                  <button
                    onClick={() => setActiveTab('video')}
                    className={`flex-1 py-3 font-semibold text-sm uppercase tracking-wider ${activeTab === 'video' ? 'text-slate-900 border-b-2 border-slate-900 bg-slate-50' : 'text-slate-400'}`}
                  >
                    Video
                  </button>
                  <button
                    onClick={() => setActiveTab('transcript')}
                    className={`flex-1 py-3 font-semibold text-sm uppercase tracking-wider ${activeTab === 'transcript' ? 'text-slate-900 border-b-2 border-slate-900 bg-slate-50' : 'text-slate-400'}`}
                  >
                    Transcript
                  </button>
                </div>

                {/* Transcript Header */}
                <div className="p-5 border-b border-slate-100 flex justify-between items-center bg-white">
                  <h3 className="font-bold text-slate-900 flex items-center gap-2 text-lg">
                    <FiFileText className="text-amber-500" />
                    Transcript
                  </h3>
                  {fullTranscript && (
                    <button
                      onClick={() => downloadTranscript(fullTranscript.transcript_text, selectedVideo.filename)}
                      className="text-xs bg-slate-900 hover:bg-black text-white px-4 py-2 rounded-full flex items-center gap-2 transition-all shadow-md hover:shadow-lg font-medium"
                    >
                      <FiDownload className="w-3 h-3" />
                      Download
                    </button>
                  )}
                </div>

                {/* Transcript Text */}
                <div className="flex-1 overflow-y-auto p-6 custom-scrollbar bg-slate-50/50">
                  {fullTranscript ? (
                    <div className="space-y-6">
                      <div className="text-xs font-medium text-slate-400 flex justify-between uppercase tracking-wider">
                        <span>Language: {fullTranscript.language?.toUpperCase()}</span>
                        <span>Model: {fullTranscript.model_used}</span>
                      </div>
                      {fullTranscript.segments && fullTranscript.segments.length > 0 ? (
                        <div className="space-y-4">
                          {fullTranscript.segments.map((segment, index) => (
                            <div key={index} className="flex gap-4 hover:bg-white p-3 rounded-xl transition-all border border-transparent hover:border-slate-100 hover:shadow-sm group">
                              <span className="text-amber-600 font-mono text-xs mt-1.5 select-none shrink-0 opacity-60 group-hover:opacity-100 transition-opacity bg-amber-50 px-2 py-0.5 rounded h-fit">
                                {formatTime(segment.start)}
                              </span>
                              <p className="text-slate-700 leading-relaxed text-sm md:text-base font-urdu" dir="auto">
                                {segment.text}
                              </p>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-slate-700 leading-relaxed whitespace-pre-wrap text-sm md:text-base font-urdu p-4 bg-white rounded-xl border border-slate-100 shadow-sm" dir="auto">
                          {fullTranscript.transcript_text}
                        </p>
                      )}
                    </div>
                  ) : (
                    <div className="flex flex-col items-center justify-center h-full text-slate-400">
                      {selectedVideo.has_transcription ? (
                        <>
                          <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-amber-500 mb-4"></div>
                          <p className="font-medium">Loading transcript...</p>
                        </>
                      ) : (
                        <div className="text-center p-8">
                           <FiFileText className="w-12 h-12 mx-auto mb-3 opacity-20" />
                           <p>No transcription available for this video.</p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
      </AnimatePresence>
    </div>
  );
}

export default Library;
