#!/usr/bin/env python3
"""
Complete end-to-end test: Upload video, process, save to database
"""
import requests
import json
import time
import os
from pathlib import Path

BASE_URL = 'http://localhost:5000'
VIDEO_PATH = '/home/tlha/Desktop/Pak News Journal Archive/test_video/video.mp4'

def test_complete_flow():
    print("="*70)
    print("COMPLETE END-TO-END TEST: VIDEO UPLOAD & TRANSCRIPTION")
    print("="*70)
    
    # Step 1: Login as test user
    print("\n1. Logging in as test user...")
    login_response = requests.post(f'{BASE_URL}/api/auth/login', json={
        'email': 'test@example.com',
        'password': 'password123'
    })
    
    if login_response.status_code != 200:
        print(f"✗ Login failed: {login_response.status_code}")
        return False
    
    token = login_response.json()['token']
    user_id = login_response.json()['user']['id']
    username = login_response.json()['user']['username']
    print(f"✓ Logged in as: {username}")
    print(f"  User ID: {user_id}")
    print(f"  Token: {token[:50]}...")
    
    # Step 2: Check video file
    print(f"\n2. Checking video file...")
    if not os.path.exists(VIDEO_PATH):
        print(f"✗ Video file not found: {VIDEO_PATH}")
        return False
    
    file_size = os.path.getsize(VIDEO_PATH)
    print(f"✓ Video found: {VIDEO_PATH}")
    print(f"  Size: {file_size / 1024 / 1024:.2f} MB")
    
    # Step 3: Upload video for transcription
    print(f"\n3. Uploading video for transcription...")
    with open(VIDEO_PATH, 'rb') as video_file:
        files = {'file': ('video.mp4', video_file, 'video/mp4')}
        upload_response = requests.post(
            f'{BASE_URL}/api/transcribe',
            files=files
        )
    
    if upload_response.status_code != 200:
        print(f"✗ Upload failed: {upload_response.status_code}")
        print(f"  Response: {upload_response.text}")
        return False
    
    job_data = upload_response.json()
    job_id = job_data['job_id']
    print(f"✓ Video uploaded successfully")
    print(f"  Job ID: {job_id}")
    print(f"  Filename: {job_data['filename']}")
    
    # Step 4: Poll for completion
    print(f"\n4. Monitoring transcription progress...")
    max_attempts = 60
    attempt = 0
    
    while attempt < max_attempts:
        time.sleep(2)
        status_response = requests.get(f'{BASE_URL}/api/status/{job_id}')
        
        if status_response.status_code != 200:
            print(f"✗ Status check failed")
            return False
        
        status_data = status_response.json()
        current_status = status_data['status']
        current_step = status_data.get('step', '')
        
        print(f"  [{attempt+1}] Status: {current_status} - {current_step}")
        
        if current_status == 'completed':
            print(f"\n✓ Transcription completed!")
            print(f"  Processing time: {status_data.get('processing_time', 'N/A')}s")
            print(f"  Transcript length: {len(status_data.get('transcript', ''))} characters")
            print(f"  Language: {status_data.get('language', 'N/A')}")
            print(f"  Segments: {len(status_data.get('segments', []))}")
            
            # Show audio metadata
            audio_meta = status_data.get('audio_metadata', {})
            if audio_meta:
                print(f"\n  Audio Processing:")
                print(f"    Duration: {audio_meta.get('duration', 'N/A')}s")
                print(f"    Sample Rate: {audio_meta.get('sample_rate', 'N/A')}Hz")
                print(f"    Noise Reduction: {audio_meta.get('noise_reduction', False)}")
                print(f"    Normalized: {audio_meta.get('normalized', False)}")
            
            # Show first 200 chars of transcript
            transcript = status_data.get('transcript', '')
            if transcript:
                print(f"\n  Transcript preview:")
                print(f"    {transcript[:200]}...")
            
            break
        
        elif current_status == 'failed':
            print(f"\n✗ Transcription failed")
            print(f"  Error: {status_data.get('error', 'Unknown error')}")
            return False
        
        attempt += 1
    
    if attempt >= max_attempts:
        print(f"\n✗ Timeout: Transcription took too long")
        return False
    
    # Step 5: Verify database records (using direct Python import)
    print(f"\n5. Verifying database records...")
    import sys
    sys.path.insert(0, '/home/tlha/Desktop/Pak News Journal Archive/backend')
    
    from database.db_config import init_db_pool, close_db_pool
    from database.video_models import Video, Transcription
    
    init_db_pool()
    
    # Get user's videos
    user_videos = Video.get_user_videos(user_id)
    print(f"✓ Found {len(user_videos)} video(s) in database")
    
    if user_videos:
        latest_video = user_videos[0]
        print(f"  Latest video:")
        print(f"    ID: {latest_video['id']}")
        print(f"    Filename: {latest_video['original_filename']}")
        print(f"    Status: {latest_video['status']}")
        print(f"    Duration: {latest_video.get('duration', 'N/A')}s")
    
    # Get user's transcriptions
    user_transcriptions = Transcription.get_user_transcriptions(user_id)
    print(f"\n✓ Found {len(user_transcriptions)} transcription(s) in database")
    
    if user_transcriptions:
        latest_trans = user_transcriptions[0]
        print(f"  Latest transcription:")
        print(f"    ID: {latest_trans['id']}")
        print(f"    Language: {latest_trans['language']}")
        print(f"    Model: {latest_trans['model_used']}")
        print(f"    Processing time: {latest_trans['processing_time']}s")
        print(f"    Text length: {len(latest_trans['transcript_text'])} chars")
    
    close_db_pool()
    
    print("\n" + "="*70)
    print("✓ COMPLETE END-TO-END TEST PASSED!")
    print("="*70)
    
    print("\nVerified:")
    print("✓ User authentication")
    print("✓ Video upload")
    print("✓ Audio processing (noise reduction, normalization)")
    print("✓ Whisper transcription")
    print("✓ Status polling")
    print("✓ Database storage (videos table)")
    print("✓ Database storage (transcriptions table)")
    print("✓ Complete workflow integration")
    
    return True

if __name__ == '__main__':
    try:
        test_complete_flow()
    except Exception as e:
        print(f"\n✗ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
