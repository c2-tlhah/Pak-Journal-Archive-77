-- ============================================================
-- PAK JOURNAL ARCHIVE 77 - DATABASE SCHEMA
-- PostgreSQL Database Schema
-- ============================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- USERS TABLE
-- ============================================================
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    role VARCHAR(20) DEFAULT 'user' CHECK (role IN ('admin', 'editor', 'user')),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Index for faster lookups
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_role ON users(role);

-- ============================================================
-- VIDEOS TABLE
-- ============================================================
CREATE TABLE videos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    original_filename VARCHAR(255) NOT NULL,
    file_size BIGINT NOT NULL,
    duration DECIMAL(10, 2),
    mime_type VARCHAR(50),
    storage_path VARCHAR(500),
    status VARCHAR(20) DEFAULT 'uploaded' CHECK (status IN ('uploaded', 'processing', 'completed', 'failed')),
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_date TIMESTAMP,
    metadata JSONB
);

-- Indexes for videos
CREATE INDEX idx_videos_user_id ON videos(user_id);
CREATE INDEX idx_videos_status ON videos(status);
CREATE INDEX idx_videos_upload_date ON videos(upload_date);

-- ============================================================
-- TRANSCRIPTIONS TABLE
-- ============================================================
CREATE TABLE transcriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    video_id UUID NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    transcript_text TEXT NOT NULL,
    language VARCHAR(10) DEFAULT 'ur',
    model_used VARCHAR(50) DEFAULT 'whisper-tiny',
    confidence_score DECIMAL(5, 4),
    segments JSONB,
    audio_metadata JSONB,
    processing_time DECIMAL(10, 2),
    status VARCHAR(20) DEFAULT 'completed' CHECK (status IN ('processing', 'completed', 'failed')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for transcriptions
CREATE INDEX idx_transcriptions_video_id ON transcriptions(video_id);
CREATE INDEX idx_transcriptions_user_id ON transcriptions(user_id);
CREATE INDEX idx_transcriptions_language ON transcriptions(language);
CREATE INDEX idx_transcriptions_created_at ON transcriptions(created_at);

-- Full text search index for transcript_text
CREATE INDEX idx_transcriptions_text_search ON transcriptions USING gin(to_tsvector('english', transcript_text));

-- ============================================================
-- TRIGGERS
-- ============================================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_transcriptions_updated_at BEFORE UPDATE ON transcriptions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- DEFAULT ADMIN USER (password: admin123)
-- ============================================================
-- Note: Password hash is for 'admin123' using bcrypt
-- Change this password immediately after first login
INSERT INTO users (username, email, password_hash, full_name, role) 
VALUES (
    'admin',
    'admin@pakjournal77.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5RA8jVGGBVVGS',
    'System Administrator',
    'admin'
) ON CONFLICT (username) DO NOTHING;

-- ============================================================
-- VIEWS
-- ============================================================

-- View for user statistics
CREATE OR REPLACE VIEW user_stats AS
SELECT 
    u.id,
    u.username,
    u.email,
    u.role,
    COUNT(DISTINCT v.id) as total_videos,
    COUNT(DISTINCT t.id) as total_transcriptions,
    COALESCE(SUM(v.file_size), 0) as total_storage_bytes,
    MAX(v.upload_date) as last_upload_date
FROM users u
LEFT JOIN videos v ON u.id = v.user_id
LEFT JOIN transcriptions t ON u.id = t.user_id
GROUP BY u.id, u.username, u.email, u.role;

-- View for recent transcriptions
CREATE OR REPLACE VIEW recent_transcriptions AS
SELECT 
    t.id,
    t.video_id,
    u.username,
    u.email,
    v.original_filename,
    t.language,
    t.processing_time,
    t.created_at,
    LENGTH(t.transcript_text) as text_length
FROM transcriptions t
JOIN users u ON t.user_id = u.id
JOIN videos v ON t.video_id = v.id
ORDER BY t.created_at DESC;

-- ============================================================
-- COMMENTS
-- ============================================================
COMMENT ON TABLE users IS 'User accounts with role-based access control';
COMMENT ON TABLE videos IS 'Uploaded video files and metadata';
COMMENT ON TABLE transcriptions IS 'Generated transcriptions from videos';
COMMENT ON COLUMN users.role IS 'User role: admin (full access), editor (can edit), user (view only)';
COMMENT ON COLUMN videos.status IS 'Processing status of the video';
COMMENT ON COLUMN transcriptions.segments IS 'JSON array of timestamped transcript segments';
