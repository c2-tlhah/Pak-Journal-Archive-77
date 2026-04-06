import { useState, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { FiSearch, FiClock, FiUser, FiTag, FiX, FiPlay, FiCalendar, FiFileText, FiVideo } from 'react-icons/fi';
import GoldenBackground from '../components/GoldenBackground';

const API_BASE_URL = import.meta.env.PROD
  ? 'https://pak-journal-archive-77.onrender.com'
  : 'http://localhost:5000';

const ENTITY_COLORS = {
  PER: 'bg-blue-100 border-blue-300 text-blue-800',
  LOC: 'bg-green-100 border-green-300 text-green-800',
  ORG: 'bg-purple-100 border-purple-300 text-purple-800',
};

const REASON_LABELS = {
  speaker: 'Speaker',
  category: 'Category',
  entity: 'Entity',
  entity_term: 'Entity',
  tag: 'Tag',
  title: 'Title',
  transcript: 'Transcript',
  transcript_term: 'Transcript',
};

function Search() {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const navigate = useNavigate();
  const inputRef = useRef(null);

  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [searched, setSearched] = useState(false);
  const [error, setError] = useState(null);
  const [mediaModal, setMediaModal] = useState(false);
  const [selectedVideo, setSelectedVideo] = useState(null);

  if (authLoading) return null;
  if (!isAuthenticated) { navigate('/login'); return null; }

  const doSearch = async (e, overrideQuery) => {
    e?.preventDefault();
    const q = (overrideQuery || query).trim();
    if (!q) return;

    setSearching(true);
    setError(null);

    try {
      const res = await fetch(`${API_BASE_URL}/api/search?q=${encodeURIComponent(q)}&limit=20`);
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.error || 'Search request failed');
      }
      const data = await res.json();
      setResults(data.results || []);
      setSearched(true);
    } catch (err) {
      setError(err.message);
      setResults([]);
    } finally {
      setSearching(false);
    }
  };

  const clearSearch = () => {
    setQuery('');
    setResults([]);
    setSearched(false);
    setError(null);
    inputRef.current?.focus();
  };

  const formatDuration = (sec) => {
    if (!sec) return '';
    const m = Math.floor(sec / 60);
    const s = Math.round(sec % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    try { return new Date(dateStr).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' }); }
    catch { return dateStr; }
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return '';
    if (bytes >= 1073741824) return (bytes / 1073741824).toFixed(1) + ' GB';
    if (bytes >= 1048576) return (bytes / 1048576).toFixed(1) + ' MB';
    return (bytes / 1024).toFixed(0) + ' KB';
  };

  const openMediaModal = (video) => {
    setSelectedVideo(video);
    setMediaModal(true);
  };

  return (
    <>
      <GoldenBackground variant="search" />
      <div className="min-h-screen pt-28 pb-16 px-4 md:px-8 relative z-10">
        <div className="max-w-7xl mx-auto">

          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center mb-10"
          >
            <h1 className="text-3xl md:text-4xl font-bold text-white mb-2 tracking-tight">
              Search Archive
            </h1>
            <p className="text-slate-400 text-sm">
              Search by speaker, category, entity, tag, or keyword across all videos
            </p>
          </motion.div>

          {/* Search bar */}
          <motion.form
            onSubmit={doSearch}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="relative mb-8 max-w-4xl mx-auto"
          >
            <div className="flex items-center bg-slate-900/70 backdrop-blur-xl border border-slate-700/60 rounded-xl shadow-2xl overflow-hidden focus-within:border-amber-500/50 transition-colors">
              <FiSearch className="ml-4 text-slate-400 flex-shrink-0" size={20} />
              <input
                ref={inputRef}
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Nawaz Sharif  ·  economy  ·  سیاست  ·  IMF loan  ·  لاہور ..."
                dir="auto"
                className="flex-1 bg-transparent text-white placeholder:text-slate-500 text-base px-4 py-4 outline-none"
                autoFocus
              />
              {query && (
                <button type="button" onClick={clearSearch} className="text-slate-500 hover:text-slate-300 px-2">
                  <FiX size={18} />
                </button>
              )}
              <button
                type="submit"
                disabled={searching || !query.trim()}
                className="bg-gradient-to-r from-amber-500 to-amber-600 text-slate-900 font-semibold px-6 py-4 hover:from-amber-400 hover:to-amber-500 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
              >
                {searching ? (
                  <span className="flex items-center gap-2">
                    <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>
                    Searching
                  </span>
                ) : 'Search'}
              </button>
            </div>
          </motion.form>

          {/* Quick examples */}
          {!searched && !searching && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2 }}
              className="flex flex-wrap justify-center gap-2 mb-12 max-w-4xl mx-auto">
              {['Nawaz Sharif', 'economy', 'سیاست', 'Imran Khan', 'Pakistan'].map(ex => (
                <button key={ex} onClick={(e) => { setQuery(ex); doSearch(e, ex); }}
                  className="px-3 py-1.5 rounded-lg bg-slate-800/60 border border-slate-700/40 text-slate-400 text-xs hover:border-amber-500/50 hover:text-amber-400 transition-colors" dir="auto">
                  {ex}
                </button>
              ))}
            </motion.div>
          )}

          {/* Error */}
          {error && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
              className="bg-red-900/30 border border-red-700/50 rounded-lg p-4 mb-6 text-red-300 text-sm text-center max-w-4xl mx-auto">
              {error}
            </motion.div>
          )}

          {/* Results */}
          <AnimatePresence mode="wait">
            {searching && (
              <motion.div key="loading" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                className="text-center text-slate-400 py-20">
                <svg className="animate-spin h-8 w-8 mx-auto mb-3 text-amber-500" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>
                Searching the archive...
              </motion.div>
            )}

            {!searching && searched && results.length === 0 && (
              <motion.div key="empty" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                className="text-center text-slate-500 py-20">
                <FiSearch size={40} className="mx-auto mb-3 opacity-40" />
                <p className="text-lg">No results found</p>
                <p className="text-sm mt-1">Try different keywords, a speaker name, or use Urdu</p>
              </motion.div>
            )}

            {!searching && results.length > 0 && (
              <motion.div key="results" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>

                <p className="text-slate-500 text-xs mb-6">{results.length} result{results.length !== 1 ? 's' : ''}</p>

                {/* ── Library-style grid ── */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                  <AnimatePresence>
                  {results.map((video, index) => (
                    <motion.div
                      key={video.id}
                      initial={{ opacity: 0, y: 30 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, scale: 0.9 }}
                      transition={{ duration: 0.5, delay: index * 0.05 }}
                      className="bg-white/40 backdrop-blur-md border border-white/50 rounded-2xl overflow-hidden hover:border-white/80 transition-all duration-500 hover:shadow-2xl hover:shadow-amber-900/10 group cursor-pointer relative flex flex-col"
                      onClick={() => openMediaModal(video)}
                    >
                      {/* Video Thumbnail */}
                      <div className="relative aspect-video bg-slate-900 flex items-center justify-center overflow-hidden rounded-t-2xl group-hover:shadow-inner transition-all duration-500">
                        {video.video_url ? (
                          <video
                            src={`${API_BASE_URL}${video.video_url}`}
                            className="w-full h-full object-cover opacity-90 group-hover:opacity-100 group-hover:scale-105 transition-all duration-700"
                            muted
                            loop
                            onMouseOver={e => e.target.play().catch(() => {})}
                            onMouseOut={e => { e.target.pause(); e.target.currentTime = 0; }}
                          />
                        ) : (
                          <div className="w-full h-full bg-gradient-to-br from-slate-800 to-slate-900 flex items-center justify-center">
                            <FiVideo className="w-16 h-16 text-slate-600" />
                          </div>
                        )}

                        {/* Play overlay */}
                        <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500 flex items-center justify-center">
                          <div className="w-14 h-14 rounded-full bg-white/90 flex items-center justify-center shadow-xl transform scale-75 group-hover:scale-100 transition-transform duration-300">
                            <FiPlay className="w-6 h-6 text-slate-900 ml-1" />
                          </div>
                        </div>

                        {/* Duration badge */}
                        {video.duration > 0 && (
                          <div className="absolute bottom-2 right-2 flex items-center gap-1 px-2 py-1 rounded-md bg-black/70 text-white text-[10px] font-mono backdrop-blur-sm">
                            <FiClock size={10} />
                            {formatDuration(video.duration)}
                          </div>
                        )}

                        {/* Match reasons badge */}
                        {video.match_reasons && video.match_reasons.length > 0 && (
                          <div className="absolute top-2 left-2 flex flex-wrap gap-1">
                            {[...new Set(video.match_reasons.map(r => REASON_LABELS[r] || r))].map((label, i) => (
                              <span key={i} className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-amber-500/90 text-slate-900 backdrop-blur-sm">
                                {label}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>

                      {/* Card body */}
                      <div className="p-5 flex-1 flex flex-col">
                        {/* Title */}
                        <h3 className="text-lg font-bold text-slate-900 mb-3 font-urdu line-clamp-2 leading-[2] pt-0.5" dir="auto">
                          {video.original_filename || video.filename || 'Untitled Video'}
                        </h3>

                        {/* Speaker */}
                        <div className="mb-3 flex items-center gap-2">
                          <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Speaker:</span>
                          <span className={`text-sm font-medium ${video.speaker === 'Unknown Speaker' ? 'text-amber-600 italic' : 'text-slate-700'}`}>
                            {video.speaker || 'Unknown Speaker'}
                          </span>
                        </div>

                        {/* Category badge */}
                        {video.category && video.category !== 'unknown' && (
                          <div className="mb-3">
                            <span className="inline-flex items-center px-3 py-1.5 rounded-lg bg-amber-500/20 border border-amber-400/40 text-amber-800 text-xs font-bold uppercase tracking-wider shadow-sm" dir="auto">
                              {video.category}
                            </span>
                          </div>
                        )}

                        {/* Tag chips */}
                        {Array.isArray(video.tags) && video.tags.filter(t => (t.tag || t) !== 'unknown').length > 0 && (
                          <div className="flex flex-wrap gap-1.5 mb-4">
                            {video.tags.filter(t => (t.tag || t) !== 'unknown').slice(0, 10).map((tagItem, idx) => {
                              const tagText = tagItem.tag || tagItem;
                              return (
                                <span
                                  key={idx}
                                  className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-white/50 border border-slate-200/70 text-slate-600 text-[11px] font-medium shadow-sm"
                                  dir="auto"
                                >
                                  {tagText}
                                  {tagItem.source === 'ocr' && <span className="text-[8px] text-blue-500 font-bold uppercase">OCR</span>}
                                </span>
                              );
                            })}
                          </div>
                        )}

                        {/* Named entities */}
                        {Array.isArray(video.entities) && video.entities.length > 0 && (
                          <div className="flex flex-wrap gap-1.5 mb-4">
                            {video.entities.slice(0, 8).map((ent, idx) => {
                              const cls = ENTITY_COLORS[ent.entity_type] || 'bg-slate-100 border-slate-300 text-slate-700';
                              return (
                                <span key={idx} className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md border text-[11px] font-medium shadow-sm ${cls}`} dir="auto">
                                  <span className="opacity-60 text-[9px] uppercase font-bold">{ent.entity_type}</span>
                                  {ent.entity_text}
                                </span>
                              );
                            })}
                          </div>
                        )}

                        {/* Metadata */}
                        <div className="flex items-center gap-4 text-xs font-medium text-slate-500 mb-5">
                          {video.upload_date && (
                            <div className="flex items-center bg-white/40 px-2 py-1 rounded-md border border-white/30">
                              <FiCalendar className="w-3 h-3 mr-1.5 text-slate-400" />
                              <span>{formatDate(video.upload_date).split(',')[0]}</span>
                            </div>
                          )}
                          {video.file_size > 0 && (
                            <div className="flex items-center bg-white/40 px-2 py-1 rounded-md border border-white/30">
                              <FiFileText className="w-3 h-3 mr-1.5 text-slate-400" />
                              <span>{formatFileSize(video.file_size)}</span>
                            </div>
                          )}
                        </div>

                        {/* Transcript preview */}
                        {video.has_transcription && video.transcript_preview ? (
                          <div className="bg-white/30 rounded-xl p-4 mt-auto border border-white/40 group-hover:bg-white/50 transition-colors relative overflow-hidden">
                            <p className="text-slate-600 text-xs leading-[2] line-clamp-3 font-urdu pt-0.5 pb-1.5" dir="auto">
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
              </motion.div>
            )}
          </AnimatePresence>
        </div>
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
              className="bg-white rounded-3xl max-w-4xl w-full max-h-[85vh] overflow-hidden shadow-2xl flex flex-col ring-1 ring-white/20"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Modal header */}
              <div className="bg-slate-50 p-5 border-b border-slate-200 flex justify-between items-center">
                <h2 className="text-xl font-bold text-slate-900 max-w-2xl break-words font-urdu line-clamp-2 leading-[2.2] pt-1 pb-2" dir="auto">
                  {selectedVideo.original_filename || selectedVideo.filename || 'Untitled Video'}
                </h2>
                <button
                  onClick={() => setMediaModal(false)}
                  className="bg-slate-100 hover:bg-slate-200 text-slate-500 hover:text-slate-900 transition-colors rounded-full w-10 h-10 flex items-center justify-center"
                >
                  <FiX className="w-5 h-5" />
                </button>
              </div>

              {/* Modal body */}
              <div className="flex-1 overflow-y-auto">
                {selectedVideo.video_url ? (
                  <video
                    src={`${API_BASE_URL}${selectedVideo.video_url}`}
                    className="w-full aspect-video bg-black"
                    controls
                    autoPlay
                  />
                ) : (
                  <div className="w-full aspect-video bg-slate-900 flex items-center justify-center">
                    <FiVideo className="w-20 h-20 text-slate-600" />
                  </div>
                )}

                <div className="p-6 space-y-4">
                  {/* Speaker + Category */}
                  <div className="flex flex-wrap items-center gap-3">
                    {selectedVideo.speaker && selectedVideo.speaker !== 'Unknown Speaker' && (
                      <span className="flex items-center gap-1.5 text-sm text-slate-700">
                        <FiUser size={14} className="text-slate-400" /> {selectedVideo.speaker}
                      </span>
                    )}
                    {selectedVideo.category && selectedVideo.category !== 'unknown' && (
                      <span className="inline-flex items-center px-3 py-1 rounded-lg bg-amber-500/20 border border-amber-400/40 text-amber-800 text-xs font-bold uppercase" dir="auto">
                        {selectedVideo.category}
                      </span>
                    )}
                  </div>

                  {/* Transcript */}
                  {selectedVideo.transcript_preview && (
                    <div className="bg-slate-50 rounded-xl p-4 border border-slate-200">
                      <p className="text-slate-700 text-sm leading-[2] font-urdu" dir="auto">
                        {selectedVideo.transcript_preview}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}

export default Search;

