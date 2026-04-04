"""
Video and Transcription database operations
"""
from typing import Optional, Dict, Any, List
import logging
import json
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
                logger.info(f"[OK] Video record created: {video_id} ({original_filename})")
                return video_id
        except Exception as e:
            logger.error(f"[FAIL] Failed to create video record: {e}")
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
                logger.info(f"[OK] Video status updated: {video_id} -> {status}")
        except Exception as e:
            logger.error(f"[FAIL] Failed to update video status: {e}")
    
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
            logger.error(f"[FAIL] Failed to get video: {e}")
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
            logger.error(f"[FAIL] Failed to get user videos: {e}")
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
                logger.info(f"[OK] Video title updated: {video_id} -> {title}")
                return True
        except Exception as e:
            logger.error(f"[FAIL] Failed to update video title: {e}")
            return False

    @staticmethod
    def update_video_speaker(video_id: str, speaker: str) -> bool:
        """Update video speaker"""
        try:
            with get_db_cursor() as cursor:
                cursor.execute("""
                    UPDATE videos 
                    SET speaker = %s
                    WHERE id = %s
                """, (speaker, video_id))
                logger.info(f"[OK] Video speaker updated: {video_id} -> {speaker}")
                return True
        except Exception as e:
            logger.error(f"[FAIL] Failed to update video speaker: {e}")
            return False

    @staticmethod
    def update_video_tagging(video_id: str, category: str,
                             tags: list, frontend_payload: dict) -> bool:
        """Save tagging pipeline results: category, tags, and composed frontend_payload"""
        try:
            with get_db_cursor() as cursor:
                cursor.execute("""
                    UPDATE videos
                    SET category = %s,
                        tags = %s,
                        frontend_payload = %s
                    WHERE id = %s
                """, (
                    category,
                    json.dumps(tags),
                    json.dumps(frontend_payload),
                    video_id,
                ))
                logger.info(f"[OK] Video tagging saved: {video_id} category={category}")
                return True
        except Exception as e:
            logger.error(f"[FAIL] Failed to save video tagging: {e}")
            return False
    
    @staticmethod
    def delete_video(video_id: str) -> bool:
        """Delete a video record"""
        try:
            with get_db_cursor() as cursor:
                cursor.execute("""
                    DELETE FROM videos WHERE id = %s
                """, (video_id,))
                logger.info(f"[OK] Video record deleted: {video_id}")
                return True
        except Exception as e:
            logger.error(f"[FAIL] Failed to delete video record: {e}")
            return False

    @staticmethod
    def get_video_tags(video_id: str) -> list:
        """Get tags for a video"""
        try:
            with get_db_cursor(commit=False) as cursor:
                cursor.execute("SELECT tags FROM videos WHERE id = %s", (video_id,))
                row = cursor.fetchone()
                if row and row['tags']:
                    tags = row['tags']
                    return tags if isinstance(tags, list) else json.loads(tags)
                return []
        except Exception as e:
            logger.error(f"[FAIL] Failed to get video tags: {e}")
            return []

    @staticmethod
    def update_video_tags(video_id: str, tags: list) -> bool:
        """Replace all tags for a video"""
        try:
            with get_db_cursor() as cursor:
                cursor.execute("""
                    UPDATE videos
                    SET tags = %s
                    WHERE id = %s
                """, (json.dumps(tags), video_id))
                logger.info(f"[OK] Video tags updated: {video_id} ({len(tags)} tags)")
                return True
        except Exception as e:
            logger.error(f"[FAIL] Failed to update video tags: {e}")
            return False

    @staticmethod
    def add_video_tag(video_id: str, tag: str, confidence: float = 1.0, source: str = "manual") -> bool:
        """Add a single tag to a video (appends if not already present)"""
        try:
            existing = Video.get_video_tags(video_id)
            if any(t.get("tag") == tag for t in existing):
                return True  # already exists
            existing.append({"tag": tag, "confidence": confidence, "source": source})
            return Video.update_video_tags(video_id, existing)
        except Exception as e:
            logger.error(f"[FAIL] Failed to add video tag: {e}")
            return False

    @staticmethod
    def delete_video_tag(video_id: str, tag: str) -> bool:
        """Remove a specific tag from a video"""
        try:
            existing = Video.get_video_tags(video_id)
            updated = [t for t in existing if t.get("tag") != tag]
            return Video.update_video_tags(video_id, updated)
        except Exception as e:
            logger.error(f"[FAIL] Failed to delete video tag: {e}")
            return False

    @staticmethod
    def edit_video_tag(video_id: str, old_tag: str, new_tag: str) -> bool:
        """Rename a tag on a video"""
        try:
            existing = Video.get_video_tags(video_id)
            for t in existing:
                if t.get("tag") == old_tag:
                    t["tag"] = new_tag
                    break
            return Video.update_video_tags(video_id, existing)
        except Exception as e:
            logger.error(f"[FAIL] Failed to edit video tag: {e}")
            return False

    @staticmethod
    def update_video_category(video_id: str, category: str) -> bool:
        """Update the category for a video"""
        try:
            with get_db_cursor() as cursor:
                cursor.execute("""
                    UPDATE videos SET category = %s WHERE id = %s
                """, (category, video_id))
                logger.info(f"[OK] Video category updated: {video_id} -> {category}")
                return True
        except Exception as e:
            logger.error(f"[FAIL] Failed to update video category: {e}")
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
                logger.info(f"[OK] Transcription saved: {transcription_id} (video: {video_id})")
                return transcription_id
        except Exception as e:
            logger.error(f"[FAIL] Failed to create transcription: {e}")
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
            logger.error(f"[FAIL] Failed to get transcription: {e}")
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
            logger.error(f"[FAIL] Failed to get user transcriptions: {e}")
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
            logger.error(f"[FAIL] Failed to search transcriptions: {e}")
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
            # Ensure classification_data is JSON serialized
            if classification_data and isinstance(classification_data, dict):
                classification_data = json.dumps(classification_data)

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
                logger.info(f"[OK] Politician classification saved: {classification_id} ({politician_name} - {confidence_score:.1f}%)")
                return classification_id
        except Exception as e:
            logger.error(f"[FAIL] Failed to create politician classification: {e}")
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
            logger.error(f"[FAIL] Failed to get classifications for video {video_id}: {e}")
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
            logger.error(f"[FAIL] Failed to get classifications for user {user_id}: {e}")
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
            logger.error(f"[FAIL] Failed to get politician stats for video {video_id}: {e}")
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

                logger.info(f"[OK] Deleted classifications for video: {video_id}")
                return True
        except Exception as e:
            logger.error(f"[FAIL] Failed to delete classifications for video {video_id}: {e}")
            return False


class Entity:
    """Named entity model for database operations"""

    @staticmethod
    def get_by_video_id(video_id: str) -> List[Dict[str, Any]]:
        """Get all named entities for a video"""
        try:
            with get_db_cursor(commit=False) as cursor:
                cursor.execute("""
                    SELECT entity_text, entity_type, mention_count, mentioned_by_speakers
                    FROM entities
                    WHERE video_id = %s
                    ORDER BY mention_count DESC
                """, (video_id,))
                entities = cursor.fetchall()
                return [dict(e) for e in entities]
        except Exception as e:
            logger.error(f"[FAIL] Failed to get entities for video {video_id}: {e}")
            return []

    @staticmethod
    def add_entity(video_id: str, user_id: str, entity_text: str, entity_type: str) -> bool:
        """Add a new named entity"""
        try:
            with get_db_cursor(commit=True) as cursor:
                cursor.execute("""
                    INSERT INTO entities (video_id, user_id, entity_text, entity_type, mention_count)
                    VALUES (%s, %s, %s, %s, 1)
                    ON CONFLICT (video_id, entity_text, entity_type) DO NOTHING
                """, (video_id, user_id, entity_text, entity_type))
                return True
        except Exception as e:
            logger.error(f"[FAIL] Failed to add entity for video {video_id}: {e}")
            return False

    @staticmethod
    def edit_entity(video_id: str, old_text: str, old_type: str, new_text: str, new_type: str) -> bool:
        """Edit (rename) a named entity"""
        try:
            with get_db_cursor(commit=True) as cursor:
                cursor.execute("""
                    UPDATE entities
                    SET entity_text = %s, entity_type = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE video_id = %s AND entity_text = %s AND entity_type = %s
                """, (new_text, new_type, video_id, old_text, old_type))
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"[FAIL] Failed to edit entity for video {video_id}: {e}")
            return False

    @staticmethod
    def delete_entity(video_id: str, entity_text: str, entity_type: str) -> bool:
        """Delete a named entity"""
        try:
            with get_db_cursor(commit=True) as cursor:
                cursor.execute("""
                    DELETE FROM entities
                    WHERE video_id = %s AND entity_text = %s AND entity_type = %s
                """, (video_id, entity_text, entity_type))
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"[FAIL] Failed to delete entity for video {video_id}: {e}")
            return False
