import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { FiVideo, FiClock, FiCalendar, FiDownload, FiEye, FiFileText, FiPlay, FiTrash2 } from 'react-icons/fi';

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
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-purple-500 mx-auto"></div>
          <p className="text-white mt-4 text-lg">Loading your videos...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null; // Will redirect to login
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 py-20 px-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="text-center mb-12"
        >
          <h1 className="text-5xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-400 via-pink-400 to-purple-400 mb-4">
            Video Library
          </h1>
          <p className="text-gray-300 text-lg">
            Browse and manage your transcribed videos
          </p>
          <div className="mt-4 text-purple-300">
            <span className="font-semibold">{videos.length}</span> videos in your library
          </div>
        </motion.div>

        {/* Error Message */}
        {error && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="bg-red-500/20 border border-red-500 text-red-300 px-6 py-4 rounded-lg mb-8 text-center"
          >
            <p className="mb-4">{error}</p>
            <button
              onClick={fetchVideos}
              className="bg-red-600 hover:bg-red-700 text-white px-6 py-2 rounded-lg font-semibold transition-all duration-300"
            >
              Retry
            </button>
          </motion.div>
        )}

        {/* Videos Grid */}
        {videos.length === 0 ? (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center py-20"
          >
            <FiVideo className="w-24 h-24 text-gray-600 mx-auto mb-6" />
            <h3 className="text-2xl font-semibold text-gray-400 mb-4">No videos yet</h3>
            <p className="text-gray-500 mb-8">Start by uploading and transcribing your first video</p>
            <a
              href="/transcribe"
              className="inline-block bg-gradient-to-r from-purple-600 to-pink-600 text-white px-8 py-3 rounded-lg font-semibold hover:from-purple-700 hover:to-pink-700 transition-all duration-300"
            >
              Upload Video
            </a>
          </motion.div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {videos.map((video, index) => (
              <motion.div
                key={video.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className="bg-gradient-to-br from-purple-900/40 to-pink-900/40 backdrop-blur-sm border border-purple-500/30 rounded-xl overflow-hidden hover:border-purple-400 transition-all duration-300 hover:shadow-2xl hover:shadow-purple-500/20 group cursor-pointer"
                onClick={() => openMediaModal(video)}
              >
                {/* Video Thumbnail/Icon */}
                <div className="relative aspect-video bg-black flex items-center justify-center overflow-hidden">
                  {video.video_url ? (
                    <video 
                      src={`${API_BASE_URL}${video.video_url}`}
                      className="w-full h-full object-cover opacity-80 group-hover:opacity-100 transition-opacity duration-300"
                      muted
                      loop
                      onMouseOver={e => e.target.play().catch(() => {})}
                      onMouseOut={e => {
                        e.target.pause();
                        e.target.currentTime = 0;
                      }}
                    />
                  ) : (
                    <div className="w-full h-full bg-gradient-to-br from-purple-800/50 to-pink-800/50 flex items-center justify-center">
                      <FiVideo className="w-20 h-20 text-purple-300" />
                    </div>
                  )}
                  
                  {/* Play Overlay */}
                  <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-300 bg-black/30">
                    <div className="bg-white/20 backdrop-blur-sm p-4 rounded-full">
                      <FiPlay className="w-8 h-8 text-white fill-current" />
                    </div>
                  </div>

                  {video.status === 'completed' && (
                    <div className="absolute top-3 right-3 bg-green-500 text-white text-xs px-3 py-1 rounded-full font-semibold z-10">
                      Completed
                    </div>
                  )}
                  {video.status === 'processing' && (
                    <div className="absolute top-3 right-3 bg-yellow-500 text-white text-xs px-3 py-1 rounded-full font-semibold animate-pulse z-10">
                      Processing
                    </div>
                  )}
                </div>

                {/* Video Info */}
                <div className="p-6">
                  <h3 className="text-xl font-bold text-white mb-3 truncate" title={video.filename}>
                    {video.filename}
                  </h3>

                  {/* Stats */}
                  <div className="space-y-2 mb-4">
                    <div className="flex items-center text-gray-300 text-sm">
                      <FiClock className="w-4 h-4 mr-2 text-purple-400" />
                      <span>Duration: {formatDuration(video.duration)}</span>
                    </div>
                    <div className="flex items-center text-gray-300 text-sm">
                      <FiCalendar className="w-4 h-4 mr-2 text-purple-400" />
                      <span>{formatDate(video.upload_date)}</span>
                    </div>
                    <div className="flex items-center text-gray-300 text-sm">
                      <FiFileText className="w-4 h-4 mr-2 text-purple-400" />
                      <span>Size: {formatFileSize(video.file_size)}</span>
                    </div>
                  </div>

                  {/* Transcript Preview */}
                  {video.has_transcription && video.transcript_preview && (
                    <div className="bg-black/30 rounded-lg p-4 mb-4">
                      <p className="text-gray-300 text-sm line-clamp-3">
                        {video.transcript_preview}
                      </p>
                      <div className="mt-2 text-xs text-purple-300">
                        {video.transcript_word_count} words • {video.transcript_language.toUpperCase()}
                      </div>
                    </div>
                  )}

                  {!video.has_transcription && (
                    <div className="bg-yellow-500/20 border border-yellow-500/50 rounded-lg p-3 mb-4">
                      <p className="text-yellow-300 text-sm">No transcription available</p>
                    </div>
                  )}

                  {/* Actions */}
                  <div className="flex gap-2" onClick={e => e.stopPropagation()}>
                    {video.has_transcription ? (
                      <>
                        <button
                          onClick={() => openMediaModal(video, 'transcript')}
                          className="flex-1 bg-gradient-to-r from-purple-600 to-pink-600 text-white px-4 py-2 rounded-lg font-semibold hover:from-purple-700 hover:to-pink-700 transition-all duration-300 flex items-center justify-center gap-2"
                        >
                          <FiEye className="w-4 h-4" />
                          View
                        </button>
                        <button
                          onClick={() => {
                            if (fullTranscript && fullTranscript.transcript_text) {
                              downloadTranscript(fullTranscript.transcript_text, video.filename);
                            } else {
                              openMediaModal(video, 'transcript').then(() => {
                                // Download logic would need transcript loaded
                              });
                            }
                          }}
                          className="bg-purple-700/50 text-white px-4 py-2 rounded-lg font-semibold hover:bg-purple-600 transition-all duration-300 flex items-center justify-center"
                        >
                          <FiDownload className="w-4 h-4" />
                        </button>
                      </>
                    ) : (
                      <div className="flex-1"></div>
                    )}
                    <button
                      onClick={(e) => deleteVideo(video.id, e)}
                      className="bg-red-500/20 text-red-400 px-4 py-2 rounded-lg font-semibold hover:bg-red-500/30 transition-all duration-300 flex items-center justify-center"
                      title="Delete Video"
                    >
                      <FiTrash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>

      {/* Media Modal */}
      {mediaModal && selectedVideo && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="fixed inset-0 bg-black/90 backdrop-blur-sm z-50 flex items-center justify-center p-4"
          onClick={() => setMediaModal(false)}
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="bg-gradient-to-br from-slate-900 to-purple-900 border border-purple-500/50 rounded-2xl max-w-6xl w-full h-[85vh] overflow-hidden shadow-2xl flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="bg-gradient-to-r from-purple-800/50 to-pink-800/50 p-4 border-b border-purple-500/30 flex justify-between items-center">
              <h2 className="text-xl font-bold text-white truncate max-w-2xl">{selectedVideo.filename}</h2>
              <div className="flex gap-2 items-center">
                <button
                  onClick={(e) => deleteVideo(selectedVideo.id, e)}
                  className="text-red-400 hover:text-red-300 transition-colors p-2 rounded-full hover:bg-red-500/20 mr-2"
                  title="Delete Video"
                >
                  <FiTrash2 className="w-5 h-5" />
                </button>
                <button
                  onClick={() => setMediaModal(false)}
                  className="text-gray-400 hover:text-white transition-colors text-2xl font-bold w-8 h-8 flex items-center justify-center"
                >
                  ×
                </button>
              </div>
            </div>

            {/* Modal Content */}
            <div className="flex-1 flex flex-col md:flex-row overflow-hidden">
              {/* Video Player Section */}
              <div className={`flex-1 bg-black flex items-center justify-center relative ${activeTab === 'transcript' ? 'hidden md:flex' : ''}`}>
                {selectedVideo.video_url ? (
                  <video 
                    src={`${API_BASE_URL}${selectedVideo.video_url}`}
                    className="w-full h-full max-h-[calc(85vh-60px)] object-contain"
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
              <div className={`w-full md:w-[400px] lg:w-[500px] bg-slate-900/80 border-l border-purple-500/30 flex flex-col ${activeTab === 'video' ? 'hidden md:flex' : ''}`}>
                {/* Tabs for Mobile */}
                <div className="flex md:hidden border-b border-purple-500/30">
                  <button
                    onClick={() => setActiveTab('video')}
                    className={`flex-1 py-3 font-semibold ${activeTab === 'video' ? 'text-purple-400 border-b-2 border-purple-400' : 'text-gray-400'}`}
                  >
                    Video
                  </button>
                  <button
                    onClick={() => setActiveTab('transcript')}
                    className={`flex-1 py-3 font-semibold ${activeTab === 'transcript' ? 'text-purple-400 border-b-2 border-purple-400' : 'text-gray-400'}`}
                  >
                    Transcript
                  </button>
                </div>

                {/* Transcript Header */}
                <div className="p-4 border-b border-purple-500/30 flex justify-between items-center bg-slate-800/50">
                  <h3 className="font-bold text-white flex items-center gap-2">
                    <FiFileText className="text-purple-400" />
                    Transcript
                  </h3>
                  {fullTranscript && (
                    <button
                      onClick={() => downloadTranscript(fullTranscript.transcript_text, selectedVideo.filename)}
                      className="text-xs bg-purple-600 hover:bg-purple-700 text-white px-3 py-1.5 rounded flex items-center gap-1 transition-colors"
                    >
                      <FiDownload className="w-3 h-3" />
                      Download
                    </button>
                  )}
                </div>

                {/* Transcript Text */}
                <div className="flex-1 overflow-y-auto p-6 custom-scrollbar">
                  {fullTranscript ? (
                    <div className="space-y-4">
                      <div className="text-xs text-gray-400 mb-2 flex justify-between">
                        <span>Language: {fullTranscript.language?.toUpperCase()}</span>
                        <span>Model: {fullTranscript.model_used}</span>
                      </div>
                      {fullTranscript.segments && fullTranscript.segments.length > 0 ? (
                        <div className="space-y-4">
                          {fullTranscript.segments.map((segment, index) => (
                            <div key={index} className="flex gap-3 hover:bg-white/5 p-2 rounded transition-colors group">
                              <span className="text-purple-400 font-mono text-xs mt-1 select-none shrink-0 opacity-70 group-hover:opacity-100 transition-opacity">
                                {formatTime(segment.start)}
                              </span>
                              <p className="text-gray-200 leading-relaxed text-sm md:text-base">
                                {segment.text}
                              </p>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-gray-200 leading-relaxed whitespace-pre-wrap text-sm md:text-base">
                          {fullTranscript.transcript_text}
                        </p>
                      )}
                    </div>
                  ) : (
                    <div className="flex flex-col items-center justify-center h-full text-gray-500">
                      {selectedVideo.has_transcription ? (
                        <>
                          <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-purple-500 mb-4"></div>
                          <p>Loading transcript...</p>
                        </>
                      ) : (
                        <p>No transcription available for this video.</p>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </div>
  );
}

export default Library;
