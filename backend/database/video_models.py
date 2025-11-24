"""
Video and Transcription database operations
"""
from typing import Optional, Dict, Any, List
import logging
from database.db_config import get_db_cursor

logger = logging.getLogger(__name__)

class Video:
    """Video model for database operations"""
    
    @staticmethod
    def create_video(user_id: str, original_filename: str, file_size: int, 
                     mime_type: str = None, storage_path: str = None) -> Optional[str]:
        """Create a new video record and return video_id"""
        try:
            with get_db_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO videos (user_id, original_filename, file_size, mime_type, storage_path, status)
                    VALUES (%s, %s, %s, %s, %s, 'uploaded')
                    RETURNING id
                """, (user_id, original_filename, file_size, mime_type, storage_path))
                
                result = cursor.fetchone()
                video_id = str(result['id'])
                logger.info(f"✓ Video record created: {video_id} ({original_filename})")
                return video_id
        except Exception as e:
            logger.error(f"✗ Failed to create video record: {e}")
            return None
    
    @staticmethod
    def update_video_status(video_id: str, status: str, duration: float = None, 
                           processed_date: str = None, metadata: dict = None):
        """Update video processing status"""
        try:
            with get_db_cursor() as cursor:
                if processed_date and duration:
                    cursor.execute("""
                        UPDATE videos 
                        SET status = %s, duration = %s, processed_date = %s, metadata = %s
                        WHERE id = %s
                    """, (status, duration, processed_date, metadata, video_id))
                else:
                    cursor.execute("""
                        UPDATE videos 
                        SET status = %s
                        WHERE id = %s
                    """, (status, video_id))
                logger.info(f"✓ Video status updated: {video_id} -> {status}")
        except Exception as e:
            logger.error(f"✗ Failed to update video status: {e}")
    
    @staticmethod
    def get_video_by_id(video_id: str) -> Optional[Dict[str, Any]]:
        """Get video by ID"""
        try:
            with get_db_cursor(commit=False) as cursor:
                cursor.execute("""
                    SELECT * FROM videos WHERE id = %s
                """, (video_id,))
                
                video = cursor.fetchone()
                return dict(video) if video else None
        except Exception as e:
            logger.error(f"✗ Failed to get video: {e}")
            return None
    
    @staticmethod
    def get_user_videos(user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all videos for a user"""
        try:
            with get_db_cursor(commit=False) as cursor:
                cursor.execute("""
                    SELECT v.*, 
                           (SELECT COUNT(*) FROM transcriptions WHERE video_id = v.id) as transcription_count
                    FROM videos v
                    WHERE v.user_id = %s
                    ORDER BY v.upload_date DESC
                    LIMIT %s
                """, (user_id, limit))
                
                videos = cursor.fetchall()
                return [dict(video) for video in videos]
        except Exception as e:
            logger.error(f"✗ Failed to get user videos: {e}")
            return []

class Transcription:
    """Transcription model for database operations"""
    
    @staticmethod
    def create_transcription(video_id: str, user_id: str, transcript_text: str,
                            language: str, model_used: str, segments: list,
                            audio_metadata: dict, processing_time: float) -> Optional[str]:
        """Create a new transcription record"""
        try:
            with get_db_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO transcriptions 
                    (video_id, user_id, transcript_text, language, model_used, 
                     segments, audio_metadata, processing_time, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'completed')
                    RETURNING id
                """, (video_id, user_id, transcript_text, language, model_used,
                      segments, audio_metadata, processing_time))
                
                result = cursor.fetchone()
                transcription_id = str(result['id'])
                logger.info(f"✓ Transcription saved: {transcription_id} (video: {video_id})")
                return transcription_id
        except Exception as e:
            logger.error(f"✗ Failed to create transcription: {e}")
            return None
    
    @staticmethod
    def get_transcription_by_video_id(video_id: str) -> Optional[Dict[str, Any]]:
        """Get transcription for a video"""
        try:
            with get_db_cursor(commit=False) as cursor:
                cursor.execute("""
                    SELECT * FROM transcriptions 
                    WHERE video_id = %s 
                    ORDER BY created_at DESC 
                    LIMIT 1
                """, (video_id,))
                
                transcription = cursor.fetchone()
                return dict(transcription) if transcription else None
        except Exception as e:
            logger.error(f"✗ Failed to get transcription: {e}")
            return None
    
    @staticmethod
    def get_user_transcriptions(user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all transcriptions for a user"""
        try:
            with get_db_cursor(commit=False) as cursor:
                cursor.execute("""
                    SELECT t.*, v.original_filename, v.duration
                    FROM transcriptions t
                    JOIN videos v ON t.video_id = v.id
                    WHERE t.user_id = %s
                    ORDER BY t.created_at DESC
                    LIMIT %s
                """, (user_id, limit))
                
                transcriptions = cursor.fetchall()
                return [dict(t) for t in transcriptions]
        except Exception as e:
            logger.error(f"✗ Failed to get user transcriptions: {e}")
            return []
    
    @staticmethod
    def search_transcriptions(user_id: str, search_text: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search transcriptions by text content"""
        try:
            with get_db_cursor(commit=False) as cursor:
                cursor.execute("""
                    SELECT t.*, v.original_filename, v.duration,
                           ts_rank(to_tsvector('english', t.transcript_text), 
                                   plainto_tsquery('english', %s)) as rank
                    FROM transcriptions t
                    JOIN videos v ON t.video_id = v.id
                    WHERE t.user_id = %s 
                    AND to_tsvector('english', t.transcript_text) @@ plainto_tsquery('english', %s)
                    ORDER BY rank DESC, t.created_at DESC
                    LIMIT %s
                """, (search_text, user_id, search_text, limit))
                
                results = cursor.fetchall()
                return [dict(r) for r in results]
        except Exception as e:
            logger.error(f"✗ Failed to search transcriptions: {e}")
            return []
