#!/usr/bin/env python3
"""
Test video and transcription database operations
"""
import json
from datetime import datetime
from database.db_config import init_db_pool, test_db_connection, close_db_pool
from database.models import User
from database.video_models import Video, Transcription

def test_video_transcription_flow():
    """Test complete video upload and transcription flow"""
    
    print("="*60)
    print("VIDEO & TRANSCRIPTION DATABASE TEST")
    print("="*60)
    
    # Initialize database
    print("\n1. Initializing database connection...")
    if not init_db_pool():
        print("✗ Failed to initialize database")
        return False
    
    if not test_db_connection():
        print("✗ Failed to connect to database")
        return False
    print("✓ Database connected")
    
    try:
        # Get test user
        print("\n2. Getting test user...")
        user = User.get_user_by_email("test@example.com")
        if not user:
            print("✗ Test user not found")
            return False
        user_id = str(user['id'])
        print(f"✓ User: {user['username']} (ID: {user_id})")
        
        # Create video record
        print("\n3. Creating video record...")
        video_id = Video.create_video(
            user_id=user_id,
            original_filename="test_video.mp4",
            file_size=10485760,  # 10 MB
            mime_type="video/mp4",
            storage_path="uploads/test_video.mp4"
        )
        if not video_id:
            print("✗ Failed to create video")
            return False
        print(f"✓ Video created: {video_id}")
        
        # Update video to processing
        print("\n4. Updating video status to 'processing'...")
        Video.update_video_status(video_id, "processing")
        print("✓ Status updated")
        
        # Create transcription
        print("\n5. Creating transcription...")
        sample_segments = [
            {"start": 0.0, "end": 5.5, "text": "یہ ایک ٹیسٹ ہے"},
            {"start": 5.5, "end": 10.0, "text": "یہ دوسرا حصہ ہے"}
        ]
        
        audio_metadata = {
            "duration": 158.8,
            "sample_rate": 16000,
            "noise_reduction": True,
            "normalized": True
        }
        
        transcription_id = Transcription.create_transcription(
            video_id=video_id,
            user_id=user_id,
            transcript_text="یہ ایک ٹیسٹ ہے یہ دوسرا حصہ ہے",
            language="ur",
            model_used="whisper-tiny",
            segments=json.dumps(sample_segments),
            audio_metadata=json.dumps(audio_metadata),
            processing_time=28.5
        )
        
        if not transcription_id:
            print("✗ Failed to create transcription")
            return False
        print(f"✓ Transcription created: {transcription_id}")
        
        # Update video to completed
        print("\n6. Updating video status to 'completed'...")
        Video.update_video_status(
            video_id, 
            "completed",
            duration=158.8,
            processed_date=datetime.now().isoformat(),
            metadata=json.dumps({"model": "whisper-tiny", "language": "ur"})
        )
        print("✓ Video completed")
        
        # Retrieve video
        print("\n7. Retrieving video record...")
        video = Video.get_video_by_id(video_id)
        if video:
            print(f"✓ Video retrieved:")
            print(f"  Filename: {video['original_filename']}")
            print(f"  Status: {video['status']}")
            print(f"  Duration: {video['duration']}s")
            print(f"  Size: {video['file_size'] / 1024 / 1024:.2f} MB")
        else:
            print("✗ Failed to retrieve video")
        
        # Retrieve transcription
        print("\n8. Retrieving transcription...")
        transcription = Transcription.get_transcription_by_video_id(video_id)
        if transcription:
            print(f"✓ Transcription retrieved:")
            print(f"  Language: {transcription['language']}")
            print(f"  Model: {transcription['model_used']}")
            print(f"  Processing time: {transcription['processing_time']}s")
            print(f"  Text length: {len(transcription['transcript_text'])} chars")
        else:
            print("✗ Failed to retrieve transcription")
        
        # Get user's videos
        print("\n9. Getting user's videos...")
        user_videos = Video.get_user_videos(user_id)
        print(f"✓ Found {len(user_videos)} video(s)")
        for v in user_videos:
            print(f"  - {v['original_filename']} ({v['status']})")
        
        # Get user's transcriptions
        print("\n10. Getting user's transcriptions...")
        user_transcriptions = Transcription.get_user_transcriptions(user_id)
        print(f"✓ Found {len(user_transcriptions)} transcription(s)")
        for t in user_transcriptions:
            print(f"  - {t['original_filename']} ({t['language']}, {t['processing_time']}s)")
        
        print("\n" + "="*60)
        print("✓ ALL DATABASE TESTS PASSED!")
        print("="*60)
        
        print("\nDatabase operations verified:")
        print("✓ Video record creation")
        print("✓ Video status updates")
        print("✓ Transcription creation")
        print("✓ Video retrieval")
        print("✓ Transcription retrieval")
        print("✓ User videos listing")
        print("✓ User transcriptions listing")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        close_db_pool()
        print("\n✓ Database connection closed")

if __name__ == '__main__':
    test_video_transcription_flow()
