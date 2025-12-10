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

    @staticmethod
    def update_video_title(video_id: str, title: str) -> bool:
        """Update video title"""
        try:
            with get_db_cursor() as cursor:
                cursor.execute("""
                    UPDATE videos 
                    SET original_filename = %s
                    WHERE id = %s
                """, (title, video_id))
                logger.info(f"✓ Video title updated: {video_id} -> {title}")
                return True
        except Exception as e:
            logger.error(f"✗ Failed to update video title: {e}")
            return False
    
    @staticmethod
    def delete_video(video_id: str) -> bool:
        """Delete a video record"""
        try:
            with get_db_cursor() as cursor:
                cursor.execute("""
                    DELETE FROM videos WHERE id = %s
                """, (video_id,))
                logger.info(f"✓ Video record deleted: {video_id}")
                return True
        except Exception as e:
            logger.error(f"✗ Failed to delete video record: {e}")
            return False

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

class PoliticianClassification:
    """Politician classification model for database operations"""

    @staticmethod
    def create_classification(video_id: str, user_id: str, politician_name: str,
                             confidence_score: float, frame_number: int,
                             frame_timestamp: float = None, model_version: str = None,
                             classification_data: dict = None, status: str = 'completed') -> Optional[str]:
        """Create a new politician classification record"""
        try:
            with get_db_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO politician_classifications
                    (video_id, user_id, politician_name, confidence_score, frame_number,
                     frame_timestamp, model_version, classification_data, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (video_id, user_id, politician_name, confidence_score, frame_number,
                      frame_timestamp, model_version, classification_data, status))

                result = cursor.fetchone()
                classification_id = str(result['id'])
                logger.info(f"✓ Politician classification saved: {classification_id} ({politician_name} - {confidence_score:.1f}%)")
                return classification_id
        except Exception as e:
            logger.error(f"✗ Failed to create politician classification: {e}")
            return None

    @staticmethod
    def get_by_video_id(video_id: str) -> List[Dict[str, Any]]:
        """Get all classifications for a video"""
        try:
            with get_db_cursor(commit=False) as cursor:
                cursor.execute("""
                    SELECT * FROM politician_classifications
                    WHERE video_id = %s
                    ORDER BY frame_number ASC
                """, (video_id,))

                classifications = cursor.fetchall()
                return [dict(cls) for cls in classifications]
        except Exception as e:
            logger.error(f"✗ Failed to get classifications for video {video_id}: {e}")
            return []

    @staticmethod
    def get_by_user_id(user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all classifications for a user"""
        try:
            with get_db_cursor(commit=False) as cursor:
                cursor.execute("""
                    SELECT pc.*, v.original_filename
                    FROM politician_classifications pc
                    JOIN videos v ON pc.video_id = v.id
                    WHERE pc.user_id = %s
                    ORDER BY pc.created_at DESC
                    LIMIT %s
                """, (user_id, limit))

                classifications = cursor.fetchall()
                return [dict(cls) for cls in classifications]
        except Exception as e:
            logger.error(f"✗ Failed to get classifications for user {user_id}: {e}")
            return []

    @staticmethod
    def get_politician_stats(video_id: str) -> Dict[str, Any]:
        """Get politician detection statistics for a video"""
        try:
            with get_db_cursor(commit=False) as cursor:
                cursor.execute("""
                    SELECT
                        politician_name,
                        COUNT(*) as frame_count,
                        AVG(confidence_score) as avg_confidence,
                        MAX(confidence_score) as max_confidence,
                        MIN(confidence_score) as min_confidence
                    FROM politician_classifications
                    WHERE video_id = %s AND status = 'completed'
                    GROUP BY politician_name
                    ORDER BY frame_count DESC, avg_confidence DESC
                """, (video_id,))

                stats = cursor.fetchall()
                return {
                    'politicians': [dict(stat) for stat in stats],
                    'total_frames': sum(stat['frame_count'] for stat in stats)
                }
        except Exception as e:
            logger.error(f"✗ Failed to get politician stats for video {video_id}: {e}")
            return {'politicians': [], 'total_frames': 0}

    @staticmethod
    def delete_by_video_id(video_id: str) -> bool:
        """Delete all classifications for a video"""
        try:
            with get_db_cursor() as cursor:
                cursor.execute("""
                    DELETE FROM politician_classifications
                    WHERE video_id = %s
                """, (video_id,))

                logger.info(f"✓ Deleted classifications for video: {video_id}")
                return True
        except Exception as e:
            logger.error(f"✗ Failed to delete classifications for video {video_id}: {e}")
            return False
