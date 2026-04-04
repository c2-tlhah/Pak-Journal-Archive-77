import { useState, useEffect, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { motion, AnimatePresence } from 'framer-motion';
import { User, Mail, Calendar, MapPin, Phone, FileText, Save, Edit2, X, Camera, Eye, Upload } from 'lucide-react';
import GoldenBackground from '../components/GoldenBackground';

const Profile = () => {
  const { user, token } = useAuth();
  const [isEditing, setIsEditing] = useState(false);
  const [loading, setLoading] = useState(false);
  const [uploadingImage, setUploadingImage] = useState(false);
  const [showImageMenu, setShowImageMenu] = useState(false);
  const [showImageViewer, setShowImageViewer] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });
  const fileInputRef = useRef(null);
  const [formData, setFormData] = useState({
    username: '',
    full_name: '',
    birth_date: '',
    country: '',
    phone_number: '',
    bio: ''
  });

  useEffect(() => {
    if (user) {
      setFormData({
        username: user.username || '',
        full_name: user.full_name || '',
        birth_date: user.birth_date || '',
        country: user.country || '',
        phone_number: user.phone_number || '',
        bio: user.bio || ''
      });
    }
  }, [user]);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleImageUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('profile_picture', file);

    setUploadingImage(true);
    setMessage({ type: '', text: '' });

    try {
      const response = await fetch('http://localhost:5000/api/auth/profile-picture', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      const data = await response.json();

      if (response.ok) {
        setMessage({ type: 'success', text: 'Profile picture updated successfully!' });
        window.location.reload();
      } else {
        setMessage({ type: 'error', text: data.error || 'Failed to upload profile picture' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Network error. Please try again.' });
    } finally {
      setUploadingImage(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage({ type: '', text: '' });

    try {
      const response = await fetch('http://localhost:5000/api/auth/profile', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(formData)
      });

      const data = await response.json();

      if (response.ok) {
        setMessage({ type: 'success', text: 'Profile updated successfully!' });
        setIsEditing(false);
        // Ideally update user context here, but for now page reload or re-fetch would work
        window.location.reload(); 
      } else {
        setMessage({ type: 'error', text: data.error || 'Failed to update profile' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Network error. Please try again.' });
    } finally {
      setLoading(false);
    }
  };

  if (!user) return null;

  return (
    <div className="min-h-screen w-full pt-24 pb-12 px-4 font-sans text-slate-900 relative overflow-hidden">
      <GoldenBackground />
      
      <div className="max-w-4xl mx-auto relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white/80 backdrop-blur-xl rounded-3xl shadow-2xl overflow-hidden border border-white/40"
        >
          {/* Header Banner */}
          <div className="h-48 bg-gradient-to-r from-slate-900 to-slate-800 relative">
            <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/cubes.png')] opacity-10"></div>
            <div className="absolute -bottom-16 left-8 md:left-12 z-20">
              <div className="relative group">
                <div 
                  className="w-32 h-32 rounded-full bg-white p-1 shadow-xl cursor-pointer relative z-10"
                  onClick={() => user.profile_picture ? setShowImageMenu(!showImageMenu) : fileInputRef.current.click()}
                >
                  <div className="w-full h-full rounded-full bg-slate-200 flex items-center justify-center text-slate-400 text-4xl font-bold overflow-hidden relative">
                    {user.profile_picture ? (
                      <img 
                        src={`http://localhost:5000/uploads/${user.profile_picture}`} 
                        alt={user.username} 
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      user.username.charAt(0).toUpperCase()
                    )}
                    
                    {/* Hover Overlay */}
                    <div className="absolute inset-0 bg-black/50 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                      <Camera className="text-white" size={32} />
                    </div>
                  </div>
                </div>

                {/* Image Menu */}
                <AnimatePresence>
                  {showImageMenu && (
                    <motion.div
                      initial={{ opacity: 0, scale: 0.9, y: -10 }}
                      animate={{ opacity: 1, scale: 1, y: 0 }}
                      exit={{ opacity: 0, scale: 0.9, y: -10 }}
                      className="absolute top-full left-0 mt-2 w-48 bg-white rounded-xl shadow-xl border border-slate-100 overflow-hidden z-30"
                    >
                      <button
                        onClick={() => {
                          setShowImageViewer(true);
                          setShowImageMenu(false);
                        }}
                        className="w-full px-4 py-3 text-left text-slate-700 hover:bg-slate-50 flex items-center gap-3 transition-colors"
                      >
                        <Eye size={18} className="text-slate-400" />
                        View Photo
                      </button>
                      <button
                        onClick={() => {
                          fileInputRef.current.click();
                          setShowImageMenu(false);
                        }}
                        className="w-full px-4 py-3 text-left text-slate-700 hover:bg-slate-50 flex items-center gap-3 transition-colors border-t border-slate-100"
                      >
                        <Upload size={18} className="text-slate-400" />
                        Upload New
                      </button>
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* Hidden Input */}
                <input 
                  type="file" 
                  ref={fileInputRef} 
                  onChange={handleImageUpload} 
                  className="hidden" 
                  accept="image/*"
                />

                {uploadingImage && (
                  <div className="absolute inset-0 flex items-center justify-center bg-white/80 rounded-full z-20">
                    <div className="w-8 h-8 border-4 border-amber-500 border-t-transparent rounded-full animate-spin"></div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Profile Content */}
          <div className="pt-20 px-8 md:px-12 pb-12">
            <div className="flex justify-between items-start mb-8">
              <div>
                <h1 className="text-3xl font-bold text-slate-900">{user.username}</h1>
                <p className="text-slate-500 font-medium">{user.email}</p>
                <div className="mt-2 inline-flex items-center px-3 py-1 rounded-full bg-amber-100 text-amber-800 text-xs font-bold uppercase tracking-wider">
                  {user.role}
                </div>
              </div>
              
              {!isEditing && (
                <button
                  onClick={() => setIsEditing(true)}
                  className="flex items-center gap-2 px-4 py-2 bg-slate-900 text-white rounded-lg hover:bg-slate-800 transition-colors text-sm font-medium shadow-lg hover:shadow-xl hover:-translate-y-0.5"
                >
                  <Edit2 size={16} />
                  Edit Profile
                </button>
              )}
            </div>

            {message.text && (
              <div className={`mb-6 p-4 rounded-lg border ${message.type === 'success' ? 'bg-green-50 border-green-200 text-green-700' : 'bg-red-50 border-red-200 text-red-700'}`}>
                {message.text}
              </div>
            )}

            <form onSubmit={handleSubmit}>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {/* Username */}
                <div className="space-y-2">
                  <label className="flex items-center gap-2 text-sm font-bold text-slate-700 uppercase tracking-wider">
                    <User size={16} className="text-amber-500" />
                    Username
                  </label>
                  {isEditing ? (
                    <input
                      type="text"
                      name="username"
                      value={formData.username}
                      onChange={handleChange}
                      className="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500 transition-all"
                      placeholder="Enter your username"
                    />
                  ) : (
                    <p className="text-lg text-slate-900 font-medium border-b border-slate-100 pb-2">
                      {user.username || <span className="text-slate-400 italic">Not set</span>}
                    </p>
                  )}
                </div>

                {/* Full Name */}
                <div className="space-y-2">
                  <label className="flex items-center gap-2 text-sm font-bold text-slate-700 uppercase tracking-wider">
                    <User size={16} className="text-amber-500" />
                    Full Name
                  </label>
                  {isEditing ? (
                    <input
                      type="text"
                      name="full_name"
                      value={formData.full_name}
                      onChange={handleChange}
                      className="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500 transition-all"
                      placeholder="Enter your full name"
                    />
                  ) : (
                    <p className="text-lg text-slate-900 font-medium border-b border-slate-100 pb-2">
                      {user.full_name || <span className="text-slate-400 italic">Not set</span>}
                    </p>
                  )}
                </div>

                {/* Birth Date */}
                <div className="space-y-2">
                  <label className="flex items-center gap-2 text-sm font-bold text-slate-700 uppercase tracking-wider">
                    <Calendar size={16} className="text-amber-500" />
                    Birth Date
                  </label>
                  {isEditing ? (
                    <input
                      type="date"
                      name="birth_date"
                      value={formData.birth_date}
                      onChange={handleChange}
                      className="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500 transition-all"
                    />
                  ) : (
                    <p className="text-lg text-slate-900 font-medium border-b border-slate-100 pb-2">
                      {user.birth_date || <span className="text-slate-400 italic">Not set</span>}
                    </p>
                  )}
                </div>

                {/* Country */}
                <div className="space-y-2">
                  <label className="flex items-center gap-2 text-sm font-bold text-slate-700 uppercase tracking-wider">
                    <MapPin size={16} className="text-amber-500" />
                    Country
                  </label>
                  {isEditing ? (
                    <input
                      type="text"
                      name="country"
                      value={formData.country}
                      onChange={handleChange}
                      className="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500 transition-all"
                      placeholder="Enter your country"
                    />
                  ) : (
                    <p className="text-lg text-slate-900 font-medium border-b border-slate-100 pb-2">
                      {user.country || <span className="text-slate-400 italic">Not set</span>}
                    </p>
                  )}
                </div>

                {/* Phone Number */}
                <div className="space-y-2">
                  <label className="flex items-center gap-2 text-sm font-bold text-slate-700 uppercase tracking-wider">
                    <Phone size={16} className="text-amber-500" />
                    Phone Number
                  </label>
                  {isEditing ? (
                    <input
                      type="tel"
                      name="phone_number"
                      value={formData.phone_number}
                      onChange={handleChange}
                      className="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500 transition-all"
                      placeholder="Enter your phone number"
                    />
                  ) : (
                    <p className="text-lg text-slate-900 font-medium border-b border-slate-100 pb-2">
                      {user.phone_number || <span className="text-slate-400 italic">Not set</span>}
                    </p>
                  )}
                </div>

                {/* Bio - Full Width */}
                <div className="col-span-1 md:col-span-2 space-y-2">
                  <label className="flex items-center gap-2 text-sm font-bold text-slate-700 uppercase tracking-wider">
                    <FileText size={16} className="text-amber-500" />
                    Bio
                  </label>
                  {isEditing ? (
                    <textarea
                      name="bio"
                      value={formData.bio}
                      onChange={handleChange}
                      rows="4"
                      className="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500 transition-all resize-none"
                      placeholder="Tell us about yourself..."
                    />
                  ) : (
                    <p className="text-lg text-slate-900 font-medium border-b border-slate-100 pb-2 leading-relaxed">
                      {user.bio || <span className="text-slate-400 italic">No bio added yet.</span>}
                    </p>
                  )}
                </div>
              </div>

              {isEditing && (
                <div className="flex justify-end gap-4 mt-8 pt-8 border-t border-slate-100">
                  <button
                    type="button"
                    onClick={() => {
                      setIsEditing(false);
                      setFormData({
                        username: user.username || '',
                        full_name: user.full_name || '',
                        birth_date: user.birth_date || '',
                        country: user.country || '',
                        phone_number: user.phone_number || '',
                        bio: user.bio || ''
                      });
                    }}
                    className="px-6 py-3 rounded-xl text-slate-600 font-bold hover:bg-slate-100 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={loading}
                    className="px-8 py-3 bg-amber-500 text-white rounded-xl font-bold hover:bg-amber-600 transition-all shadow-lg hover:shadow-amber-500/20 flex items-center gap-2"
                  >
                    {loading ? 'Saving...' : (
                      <>
                        <Save size={18} />
                        Save Changes
                      </>
                    )}
                  </button>
                </div>
              )}
            </form>
          </div>
        </motion.div>
      </div>

      {/* Image Viewer Modal */}
      <AnimatePresence>
        {showImageViewer && user.profile_picture && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 backdrop-blur-sm p-4"
            onClick={() => setShowImageViewer(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="relative max-w-4xl max-h-[90vh] w-full h-full flex items-center justify-center"
              onClick={(e) => e.stopPropagation()}
            >
              <button
                onClick={() => setShowImageViewer(false)}
                className="absolute -top-12 right-0 text-white/70 hover:text-white transition-colors"
              >
                <X size={32} />
              </button>
              <img
                src={`http://localhost:5000/uploads/${user.profile_picture}`}
                alt={user.username}
                className="max-w-full max-h-full object-contain rounded-lg shadow-2xl"
              />
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default Profile;
