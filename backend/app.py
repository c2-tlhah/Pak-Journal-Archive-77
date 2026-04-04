import os
import uuid
import threading
import logging
import time
import json
import ffmpeg
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from utils.transcriber import initialize_model, transcribe_video, unload_model as unload_whisper
from utils.politician_classifier import classify_video_politicians, unload_classifier
from database.db_config import init_db_pool, test_db_connection, close_db_pool
from database.video_models import Video, Transcription, PoliticianClassification, Entity
from routes.auth import auth_bp, token_required
try:
    from tagging import run_tagging_pipeline
    _TAGGING_AVAILABLE = True
except ImportError as _e:
    logger_bootstrap = logging.getLogger(__name__)
    logger_bootstrap.warning(f"tagging module unavailable — skipping tagging step: {_e}")
    _TAGGING_AVAILABLE = False

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 800 * 1024 * 1024  # 800MB max upload size
CORS(app)  # Enable CORS for React frontend

# Register authentication blueprint
app.register_blueprint(auth_bp, url_prefix='/api/auth')

# Serve uploaded files (including profile pictures)
@app.route('/uploads/<path:filename>')
def serve_uploads(filename):
    return send_from_directory('uploads', filename)

# In-memory job store with thread lock for thread safety
jobs = {}
jobs_lock = threading.Lock()

# Ensure directories exist
os.makedirs('uploads', exist_ok=True)
os.makedirs('logs', exist_ok=True)
os.makedirs('processed_audio', exist_ok=True)  # For audio processing pipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/system.log', mode='a', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def validate_media_file(file_path):
    """
    Validates media file integrity and returns metadata using ffprobe
    """
    try:
        probe = ffmpeg.probe(file_path)
        video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
        audio_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'audio'), None)
        
        if not video_stream and not audio_stream:
            return False, "File contains no video or audio streams"
            
        duration = float(probe['format']['duration'])
        if duration < 10:
            return False, "Media file is too short (less than 10 seconds)"
            
        return True, {
            'duration': duration,
            'format_name': probe['format']['format_name'],
            'bit_rate': probe['format'].get('bit_rate'),
            'video_codec': video_stream['codec_name'] if video_stream else None,
            'audio_codec': audio_stream['codec_name'] if audio_stream else None
        }
    except ffmpeg.Error as e:
        error_msg = e.stderr.decode() if hasattr(e, 'stderr') and e.stderr else str(e)
        return False, f"Invalid or corrupt media file: {error_msg}"
    except Exception as e:
        return False, f"Validation error: {str(e)}"

def update_job_status(job_id, status=None, step=None, **kwargs):
    """
    Thread-safe job status update
    """
    with jobs_lock:
        if job_id in jobs:
            if status:
                jobs[job_id]['status'] = status
            if step:
                jobs[job_id]['step'] = step
                jobs[job_id]['last_update'] = datetime.now().isoformat()
            for key, value in kwargs.items():
                jobs[job_id][key] = value

def cleanup_old_files():
    """
    Cleanup files older than 1 hour from uploads directory
    Excludes profile_pictures directory and video/audio files (permanent storage)
    """
    try:
        current_time = time.time()
        for filename in os.listdir('uploads'):
            filepath = os.path.join('uploads', filename)
            
            # Skip directories (like profile_pictures)
            if os.path.isdir(filepath):
                continue
            
            # Skip video/audio files (keep them permanently)
            # These are the allowed extensions from upload_file
            video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.mp3', '.wav', '.m4a', '.flac', '.ogg'}
            file_ext = os.path.splitext(filename)[1].lower()
            if file_ext in video_extensions:
                continue
                
            if os.path.isfile(filepath):
                file_age = current_time - os.path.getmtime(filepath)
                if file_age > 3600:  # 1 hour
                    os.remove(filepath)
                    logger.info(f"Cleaned up old file: {filename}")
    except Exception as e:
        logger.error(f"Error during file cleanup: {str(e)}")

def process_file(job_id, file_path, filename, user_id=None, video_id=None):
    """
    Background thread function to process transcription
    """
    start_time = time.time()
    
    try:
        update_job_status(job_id, status='processing', step='Initializing transcription...')
        logger.info(f"[Job {job_id}] Processing started for file: {filename}")
        
        # Step 1: Validate file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_size = os.path.getsize(file_path)
        logger.info(f"[Job {job_id}] File size: {file_size / (1024*1024):.2f} MB")
        
        # Update video status to processing if video_id provided
        if video_id:
            Video.update_video_status(video_id, "processing")
        
        # Step 2: Audio Processing & Transcription (integrated pipeline)
        update_job_status(job_id, step='Processing audio (noise reduction, optimization)...')
        logger.info(f"[Job {job_id}] Starting audio processing pipeline...")
        
        # Step 3: Run Whisper transcription (now includes audio preprocessing)
        from utils.transcriber import get_model_info
        model_info = get_model_info()
        device_msg = " (using GPU)" if model_info.get('device') == 'cuda' else " (using CPU - this will be slow)"
        
        update_job_status(job_id, step=f'Transcribing to Urdu...{device_msg}')
        logger.info(f"[Job {job_id}] Starting Whisper transcription with preprocessed audio...")
        
        # Define callback to update status during transcription
        def status_callback(step):
            update_job_status(job_id, step=step)
            
        result = transcribe_video(file_path, job_id, update_status_callback=status_callback)
        
        # Step 4: Process results
        update_job_status(job_id, step='Processing transcription results...')
        logger.info(f"[Job {job_id}] Transcription completed, processing results...")
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Get audio duration from metadata
        audio_duration = result.get('audio_metadata', {}).get('duration_seconds', None)
        
        # Save to database if user_id and video_id provided
        if user_id and video_id:
            try:
                # Update video with completion info
                Video.update_video_status(
                    video_id, 
                    "completed",
                    duration=audio_duration,
                    processed_date=datetime.now().isoformat(),
                    metadata=json.dumps({
                        "model": "whisper-large-v3",
                        "language": result.get('language', 'ur'),
                        "processing_time": processing_time
                    })
                )
                
                # Save transcription
                transcription_id = Transcription.create_transcription(
                    video_id=video_id,
                    user_id=user_id,
                    transcript_text=result['text'],
                    language=result.get('language', 'ur'),
                    model_used="whisper-large-v3",
                    segments=json.dumps(result.get('segments', [])),
                    audio_metadata=json.dumps(result.get('audio_metadata', {})),
                    processing_time=processing_time
                )
                
                logger.info(f"[Job {job_id}] Saved to database - Video: {video_id}, Transcription: {transcription_id}")
                
            except Exception as db_error:
                logger.error(f"[Job {job_id}] Database save failed: {db_error}")
        
        # Step 5: Politician Classification (if video file and user authenticated)
        if user_id and video_id and os.path.exists(file_path):
            try:
                update_job_status(job_id, step='Analyzing video for politicians...')
                logger.info(f"[Job {job_id}] Starting politician classification...")
                
                # Run politician classification
                classifications = classify_video_politicians(
                    video_path=file_path,
                    video_id=video_id,
                    user_id=user_id
                )
                
                logger.info(f"[Job {job_id}] Politician classification completed: {len(classifications)} frames analyzed")
                
                # Update job status with classification info
                update_job_status(job_id, step=f'Politician analysis completed - {len(classifications)} frames analyzed')
                
            except Exception as cls_error:
                logger.error(f"[Job {job_id}] Politician classification failed: {cls_error}")
                # Don't fail the entire job if classification fails
                update_job_status(job_id, step='Politician analysis failed, but transcription completed')

        # Offload Whisper + classifier from VRAM before heavy tagging models
        if _TAGGING_AVAILABLE:
            try:
                logger.info(f"[Job {job_id}] Offloading models to free VRAM for tagging...")
                unload_whisper()
                unload_classifier()
            except Exception as ul_err:
                logger.warning(f"[Job {job_id}] Model offload issue: {ul_err}")

        # Step 6: Tagging Pipeline
        if user_id and video_id and _TAGGING_AVAILABLE:
            try:
                update_job_status(job_id, step='Running NLP tagging pipeline...')
                logger.info(f"[Job {job_id}] Starting tagging pipeline...")

                segments_raw = result.get('segments', [])
                speaker_name = Video.get_video_by_id(video_id).get('speaker', 'Unknown Speaker') if video_id else 'Unknown Speaker'

                tagging_outputs = run_tagging_pipeline(
                    transcript_segments=segments_raw,
                    speaker_name=speaker_name,
                    video_id=video_id,
                    user_id=user_id,
                    video_path=file_path,
                )

                # Extract VIDEO_TITLE from first summary sentence
                video_title = tagging_outputs.get('VIDEO_TITLE', '').strip()
                if not video_title:
                    summary_list = tagging_outputs.get('SUMMARY_LIST', [])
                    if summary_list:
                        video_title = summary_list[0].get('text', '').strip()
                if video_title:
                    Video.update_video_title(video_id, video_title)
                    update_job_status(job_id, generated_title=video_title)
                    logger.info(f"[Job {job_id}] Video title from summary: {video_title}")

                # Extract FINAL_CATEGORY and FINAL_TAGS_FLAT (already computed by pipeline)
                final_category = tagging_outputs.get('FINAL_CATEGORY', 'unknown')
                final_tags_flat = tagging_outputs.get('FINAL_TAGS_FLAT', [])

                # Compose frontend_payload — use the in-memory title, no extra DB query
                transcript_text = result.get('text', '')
                frontend_payload = {
                    'video_title': video_title,
                    'category': final_category,
                    'tags': final_tags_flat,
                    'transcript': transcript_text,
                }

                Video.update_video_tagging(
                    video_id=video_id,
                    category=final_category,
                    tags=final_tags_flat,
                    frontend_payload=frontend_payload,
                )

                logger.info(f"[Job {job_id}] Tagging pipeline complete. Category={final_category}, Tags={len(final_tags_flat)}")
                update_job_status(job_id, step='Tagging pipeline completed')

            except Exception as tag_error:
                logger.error(f"[Job {job_id}] Tagging pipeline failed: {tag_error}")
                update_job_status(job_id, step='Tagging failed, transcription still available')
        
        # Store results with metadata (including audio processing stats)
        update_job_status(
            job_id,
            status='completed',
            step='Completed successfully',
            transcript=result['text'],
            segments=result.get('segments', []),
            language=result.get('language', 'ur'),
            processing_time=f"{processing_time:.2f}s",
            completed_at=datetime.now().isoformat(),
            word_count=len(result['text'].split()) if result['text'] else 0,
            audio_metadata=result.get('audio_metadata', {}),  # Include audio processing stats
            video_id=video_id
        )
        
        logger.info(f"[Job {job_id}] Processing completed successfully in {processing_time:.2f}s")
        logger.info(f"[Job {job_id}] Transcript length: {len(result['text'])} characters")
        
        # Cleanup: Only remove processed chunks, keep original video and main audio
        try:
            # We keep the uploaded video file now
            # if os.path.exists(file_path):
            #     os.remove(file_path)
            
            # Cleanup processed audio directory - only remove chunks
            job_audio_dir = os.path.join("processed_audio", f"job_{job_id}")
            if os.path.exists(job_audio_dir):
                chunks_dir = os.path.join(job_audio_dir, "chunks")
                if os.path.exists(chunks_dir):
                    import shutil
                    shutil.rmtree(chunks_dir)
                    logger.info(f"[Job {job_id}] Cleaned up audio chunks")
                else:
                    logger.info(f"[Job {job_id}] No chunks directory found to clean")
        except Exception as e:
            logger.warning(f"[Job {job_id}] Failed to cleanup chunks: {str(e)}")
        
        # Run periodic cleanup
        cleanup_old_files()
            
    except FileNotFoundError as e:
        error_msg = f"File not found: {str(e)}"
        update_job_status(job_id, status='failed', step='Failed - File not found', error=error_msg)
        logger.error(f"[Job {job_id}] {error_msg}")
        
    except Exception as e:
        error_msg = str(e)
        update_job_status(job_id, status='failed', step='Failed - Error during processing', error=error_msg)
        logger.error(f"[Job {job_id}] Processing failed: {error_msg}", exc_info=True)
        
        # Try to cleanup file even on failure
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"[Job {job_id}] Cleaned up file after failure")
        except:
            pass

@app.route('/api/transcribe', methods=['POST'])
def upload_file():
    """
    Endpoint to upload video/audio file and start transcription
    """
    try:
        # Validate request
        if 'file' not in request.files:
            logger.warning("Upload attempt with no file")
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        if file.filename == '':
            logger.warning("Upload attempt with empty filename")
            return jsonify({"error": "Empty filename"}), 400
        
        # Validate file extension
        allowed_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.mp3', '.wav', '.m4a', '.flac', '.ogg'}
        file_extension = os.path.splitext(file.filename)[1].lower()
        
        if file_extension not in allowed_extensions:
            logger.warning(f"Invalid file type attempted: {file_extension}")
            return jsonify({
                "error": f"Invalid file type: {file_extension}",
                "allowed_types": list(allowed_extensions)
            }), 400
        
        # Extract user info from token (if provided)
        user_id = None
        video_id = None
        token = request.headers.get('Authorization')
        
        if token:
            if token.startswith('Bearer '):
                token = token[7:]
            from database.models import User
            payload = User.verify_token(token)
            if payload:
                user_id = payload.get('user_id')
                logger.info(f"Upload from authenticated user: {user_id}")
        
        # Generate unique job ID
        job_id = str(uuid.uuid4())
        
        # Save file with job ID
        save_path = os.path.join('uploads', f"{job_id}{file_extension}")
        file.save(save_path)
        
        # Validate media file integrity
        is_valid, validation_result = validate_media_file(save_path)
        if not is_valid:
            os.remove(save_path)
            logger.warning(f"Invalid media file uploaded: {validation_result}")
            return jsonify({"error": validation_result}), 400
            
        file_size = os.path.getsize(save_path)
        logger.info(f"[Job {job_id}] File uploaded and validated: {file.filename} ({file_size / (1024*1024):.2f} MB)")
        logger.info(f"[Job {job_id}] Media info: {validation_result}")
        
        # Create video record in database if user is authenticated
        if user_id:
            try:
                video_id = Video.create_video(
                    user_id=user_id,
                    original_filename=file.filename,
                    file_size=file_size,
                    mime_type=file.content_type,
                    storage_path=save_path
                )
                logger.info(f"[Job {job_id}] Video record created: {video_id}")
            except Exception as db_error:
                logger.warning(f"[Job {job_id}] Failed to create video record: {db_error}")
        
        # Initialize job with metadata
        with jobs_lock:
            jobs[job_id] = {
                'status': 'queued',
                'step': 'File uploaded, queued for processing...',
                'filename': file.filename,
                'file_size': file_size,
                'file_extension': file_extension,
                'media_info': validation_result,
                'created_at': datetime.now().isoformat(),
                'last_update': datetime.now().isoformat(),
                'user_id': user_id,
                'video_id': video_id
            }
        
        # Start background thread
        thread = threading.Thread(
            target=process_file,
            args=(job_id, save_path, file.filename, user_id, video_id),
            name=f"TranscriptionThread-{job_id[:8]}"
        )
        thread.daemon = True
        thread.start()
        
        logger.info(f"[Job {job_id}] Transcription thread started")
        
        return jsonify({
            "job_id": job_id,
            "status": "queued",
            "message": "File uploaded successfully. Transcription started.",
            "filename": file.filename,
            "video_id": video_id
        }), 200
        
    except Exception as e:
        logger.error(f"Error in upload_file: {str(e)}", exc_info=True)
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route('/api/status/<job_id>', methods=['GET'])
def get_status(job_id):
    """
    Endpoint to check transcription status
    """
    with jobs_lock:
        if job_id not in jobs:
            logger.warning(f"Status check for unknown job: {job_id}")
            return jsonify({"error": "Job not found"}), 404
        
        job = jobs[job_id].copy()  # Create a copy to avoid race conditions
    
    response = {
        "job_id": job_id,
        "status": job['status'],
        "step": job.get('step', ''),
        "filename": job.get('filename', ''),
        "created_at": job.get('created_at', ''),
        "last_update": job.get('last_update', '')
    }
    
    if job['status'] == 'completed':
        response['transcript'] = job.get('transcript', '')
        response['segments'] = job.get('segments', [])
        response['language'] = job.get('language', 'ur')
        response['processing_time'] = job.get('processing_time', '')
        response['completed_at'] = job.get('completed_at', '')
        response['word_count'] = job.get('word_count', 0)
        logger.debug(f"[Job {job_id}] Status retrieved: completed")
        
    elif job['status'] == 'failed':
        response['error'] = job.get('error', 'Unknown error')
        logger.debug(f"[Job {job_id}] Status retrieved: failed")
        
    else:
        logger.debug(f"[Job {job_id}] Status retrieved: {job['status']}")
    
    return jsonify(response), 200

@app.route('/api/logs', methods=['GET'])
def get_logs():
    """
    Endpoint to retrieve system logs
    Query params:
    - lines: number of lines to retrieve (default: 100, max: 500)
    - filter: filter logs by level (INFO, WARNING, ERROR)
    """
    try:
        log_file = 'logs/system.log'
        if not os.path.exists(log_file):
            logger.warning("Log file does not exist yet")
            return jsonify({"logs": [], "message": "No logs available yet"}), 200
        
        # Get query parameters
        num_lines = min(int(request.args.get('lines', 100)), 500)
        log_filter = request.args.get('filter', '').upper()
        
        # Read last N lines
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            last_lines = lines[-num_lines:] if len(lines) > num_lines else lines
        
        # Apply filter if specified
        if log_filter in ['INFO', 'WARNING', 'ERROR']:
            last_lines = [line for line in last_lines if f'[{log_filter}]' in line]
        
        cleaned_lines = [line.strip() for line in last_lines if line.strip()]
        
        logger.debug(f"Logs retrieved: {len(cleaned_lines)} lines")
        
        return jsonify({
            "logs": cleaned_lines,
            "total_lines": len(cleaned_lines),
            "filter_applied": log_filter if log_filter else None
        }), 200
        
    except Exception as e:
        logger.error(f"Error reading logs: {str(e)}", exc_info=True)
        return jsonify({"error": f"Failed to retrieve logs: {str(e)}"}), 500

@app.route('/api/videos/<video_id>/speaker', methods=['PUT'])
@token_required
def update_video_speaker(current_user, video_id):
    """
    Update the identified speaker for a video (Manual Override)
    """
    try:
        data = request.get_json()
        if not data or 'speaker' not in data:
            return jsonify({"error": "Speaker name is required"}), 400
            
        speaker = data['speaker']
        
        # Verify video ownership
        video = Video.get_video_by_id(video_id)
        if not video:
            return jsonify({"error": "Video not found"}), 404

        if str(video['user_id']) != current_user['user_id']:
            return jsonify({"error": "Access denied"}), 403

        # Update speaker
        success = Video.update_video_speaker(video_id, speaker)
        
        if success:
            logger.info(f"User {current_user['username']} manually updated speaker for video {video_id} to '{speaker}'")
            return jsonify({"message": "Speaker updated successfully", "speaker": speaker}), 200
        else:
            return jsonify({"error": "Failed to update speaker"}), 500

    except Exception as e:
        logger.error(f"Error updating video speaker: {str(e)}", exc_info=True)
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route('/api/videos/<video_id>/politicians', methods=['GET'])
@token_required
def get_video_politicians(current_user, video_id):
    """
    Get politician classifications for a specific video
    """
    try:
        # Verify video ownership
        video = Video.get_video_by_id(video_id)
        if not video:
            return jsonify({"error": "Video not found"}), 404

        if str(video['user_id']) != current_user['user_id']:
            return jsonify({"error": "Access denied"}), 403

        # Get classifications
        classifications = PoliticianClassification.get_by_video_id(video_id)

        # Get summary statistics
        stats = PoliticianClassification.get_politician_stats(video_id)

        return jsonify({
            "video_id": video_id,
            "classifications": classifications,
            "summary": stats,
            "total_frames": len(classifications)
        }), 200

    except Exception as e:
        logger.error(f"Error getting politician classifications: {str(e)}", exc_info=True)
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route('/api/politicians', methods=['GET'])
@token_required
def get_user_politicians(current_user):
    """
    Get all politician classifications for the current user
    Query params:
    - limit: maximum number of results (default: 100)
    """
    try:
        limit = min(int(request.args.get('limit', 100)), 500)
        classifications = PoliticianClassification.get_by_user_id(current_user['user_id'], limit)

        return jsonify({
            "classifications": classifications,
            "total_count": len(classifications),
            "limit": limit
        }), 200

    except Exception as e:
        logger.error(f"Error getting user politician classifications: {str(e)}", exc_info=True)
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route('/api/videos', methods=['GET'])
@token_required
def get_user_videos(current_user):
    """
    Get all videos for the current user with transcription info
    Query params:
    - limit: maximum number of results (default: 50)
    """
    try:
        limit = min(int(request.args.get('limit', 50)), 200)
        videos = Video.get_user_videos(current_user['user_id'], limit)
        
        # Enrich videos with transcription data
        enriched_videos = []
        for video in videos:
            # Get transcription for this video
            transcription = Transcription.get_transcription_by_video_id(str(video['id']))
            
            # Safely convert duration to float if it's Decimal
            duration = video.get('duration')
            if duration is not None:
                duration = float(duration)
            
            # Generate video URL
            storage_path = video.get('storage_path', '')
            video_url = None
            if storage_path:
                filename = os.path.basename(storage_path)
                video_url = f"/uploads/{filename}"

            video_data = {
                'id': str(video['id']),
                'filename': video.get('original_filename', 'Unknown'),
                'original_filename': video.get('original_filename', 'Unknown'),
                'file_size': int(video.get('file_size', 0)),
                'duration': duration,
                'status': video.get('status', 'uploaded'),
                'upload_date': str(video['upload_date']) if video.get('upload_date') else None,
                'processed_date': str(video['processed_date']) if video.get('processed_date') else None,
                'storage_path': storage_path,
                'video_url': video_url,
                'has_transcription': transcription is not None,
                'transcription_count': int(video.get('transcription_count', 0)),
                'speaker': video.get('speaker', 'Unknown Speaker'), # Add speaker field
                'category': video.get('category'),
                'tags': video.get('tags') or [],
                'entities': Entity.get_by_video_id(str(video['id'])),
                'frontend_payload': video.get('frontend_payload') or {},
            }
            
            # Add transcription preview if exists
            if transcription:
                transcript_text = transcription.get('transcript_text', '')
                video_data['transcript_preview'] = transcript_text[:200] + '...' if len(transcript_text) > 200 else transcript_text
                video_data['transcript_language'] = transcription.get('language', 'ur')
                video_data['transcript_word_count'] = len(transcript_text.split()) if transcript_text else 0
                video_data['transcription_id'] = str(transcription['id'])
            
            enriched_videos.append(video_data)
        
        logger.info(f"Retrieved {len(enriched_videos)} videos for user {current_user['user_id']}")
        
        return jsonify({
            "videos": enriched_videos,
            "total_count": len(enriched_videos),
            "limit": limit
        }), 200

    except Exception as e:
        logger.error(f"Error getting user videos: {str(e)}", exc_info=True)
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route('/api/videos/<video_id>/transcript', methods=['GET'])
@token_required
def get_video_transcript(current_user, video_id):
    """
    Get full transcript for a specific video
    """
    try:
        # Verify video ownership
        video = Video.get_video_by_id(video_id)
        if not video:
            return jsonify({"error": "Video not found"}), 404

        if str(video['user_id']) != current_user['user_id']:
            return jsonify({"error": "Access denied"}), 403

        # Get transcription
        transcription = Transcription.get_transcription_by_video_id(video_id)
        if not transcription:
            return jsonify({"error": "Transcription not found"}), 404

        # Parse JSON fields if they are strings
        segments = transcription.get('segments')
        if isinstance(segments, str):
            try:
                segments = json.loads(segments)
            except:
                segments = []
        
        audio_metadata = transcription.get('audio_metadata')
        if isinstance(audio_metadata, str):
            try:
                audio_metadata = json.loads(audio_metadata)
            except:
                audio_metadata = {}

        # Convert processing_time to float if it's Decimal
        processing_time = transcription.get('processing_time')
        if processing_time is not None:
            processing_time = float(processing_time)

        return jsonify({
            "video_id": video_id,
            "filename": video.get('original_filename', 'Unknown'),
            "transcription": {
                'id': str(transcription['id']),
                'transcript_text': transcription.get('transcript_text', ''),
                'language': transcription.get('language', 'ur'),
                'model_used': transcription.get('model_used', 'whisper'),
                'processing_time': processing_time,
                'created_at': str(transcription.get('created_at')) if transcription.get('created_at') else None,
                'segments': segments,
                'audio_metadata': audio_metadata
            }
        }), 200

    except Exception as e:
        logger.error(f"Error getting video transcript: {str(e)}", exc_info=True)
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route('/api/videos/<video_id>', methods=['DELETE'])
@token_required
def delete_video(current_user, video_id):
    """
    Delete a video and its associated data
    """
    try:
        # Verify video ownership
        video = Video.get_video_by_id(video_id)
        if not video:
            return jsonify({"error": "Video not found"}), 404

        if str(video['user_id']) != current_user['user_id']:
            return jsonify({"error": "Access denied"}), 403

        # Delete video (cascade will handle transcriptions and classifications)
        if Video.delete_video(video_id):
            # Also try to delete the file from storage if it exists
            if video.get('storage_path') and os.path.exists(video.get('storage_path')):
                try:
                    os.remove(video.get('storage_path'))
                except Exception as e:
                    logger.error(f"Failed to delete video file: {e}")
            
            return jsonify({"message": "Video deleted successfully"}), 200
        else:
            return jsonify({"error": "Failed to delete video"}), 500

    except Exception as e:
        logger.error(f"Error deleting video: {str(e)}", exc_info=True)
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route('/api/videos/<video_id>/rename', methods=['PUT'])
@token_required
def rename_video(video_id, user_id=None):
    """
    Rename a video
    """
    try:
        data = request.get_json()
        new_title = data.get('title', '').strip()
        
        if not new_title:
            return jsonify({"error": "Title is required"}), 400
        
        if len(new_title) > 200:
            return jsonify({"error": "Title too long (max 200 characters)"}), 400
        
        # Verify video belongs to user
        video = Video.get_video_by_id(video_id)
        if not video:
            return jsonify({"error": "Video not found"}), 404
        
        if video['user_id'] != user_id:
            return jsonify({"error": "Unauthorized"}), 403
        
        # Update title
        success = Video.update_video_title(video_id, new_title)
        
        if success:
            logger.info(f"Video renamed: {video_id} -> {new_title}")
            return jsonify({
                "message": "Video renamed successfully",
                "video_id": video_id,
                "new_title": new_title
            }), 200
        else:
            return jsonify({"error": "Failed to rename video"}), 500

    except Exception as e:
        logger.error(f"Error renaming video: {str(e)}", exc_info=True)
        return jsonify({"error": f"Server error: {str(e)}"}), 500

# ── Tag CRUD Endpoints ──────────────────────────────────────────────

@app.route('/api/videos/<video_id>/tags', methods=['GET'])
@token_required
def get_video_tags(current_user, video_id):
    """Get tags for a video"""
    try:
        video = Video.get_video_by_id(video_id)
        if not video:
            return jsonify({"error": "Video not found"}), 404
        if str(video['user_id']) != current_user['user_id']:
            return jsonify({"error": "Access denied"}), 403
        tags = Video.get_video_tags(video_id)
        return jsonify({"video_id": video_id, "tags": tags}), 200
    except Exception as e:
        logger.error(f"Error getting video tags: {e}", exc_info=True)
        return jsonify({"error": f"Server error: {str(e)}"}), 500


@app.route('/api/videos/<video_id>/tags', methods=['POST'])
@token_required
def add_video_tag(current_user, video_id):
    """Add a new tag to a video"""
    try:
        video = Video.get_video_by_id(video_id)
        if not video:
            return jsonify({"error": "Video not found"}), 404
        if str(video['user_id']) != current_user['user_id']:
            return jsonify({"error": "Access denied"}), 403

        data = request.get_json()
        tag = (data or {}).get('tag', '').strip()
        if not tag:
            return jsonify({"error": "Tag text is required"}), 400
        if len(tag) > 200:
            return jsonify({"error": "Tag too long"}), 400

        success = Video.add_video_tag(video_id, tag, source="manual")
        if success:
            return jsonify({"message": "Tag added", "tags": Video.get_video_tags(video_id)}), 200
        return jsonify({"error": "Failed to add tag"}), 500
    except Exception as e:
        logger.error(f"Error adding video tag: {e}", exc_info=True)
        return jsonify({"error": f"Server error: {str(e)}"}), 500


@app.route('/api/videos/<video_id>/tags', methods=['PUT'])
@token_required
def edit_video_tag(current_user, video_id):
    """Edit (rename) a tag on a video"""
    try:
        video = Video.get_video_by_id(video_id)
        if not video:
            return jsonify({"error": "Video not found"}), 404
        if str(video['user_id']) != current_user['user_id']:
            return jsonify({"error": "Access denied"}), 403

        data = request.get_json()
        old_tag = (data or {}).get('old_tag', '').strip()
        new_tag = (data or {}).get('new_tag', '').strip()
        if not old_tag or not new_tag:
            return jsonify({"error": "old_tag and new_tag are required"}), 400
        if len(new_tag) > 200:
            return jsonify({"error": "Tag too long"}), 400

        success = Video.edit_video_tag(video_id, old_tag, new_tag)
        if success:
            return jsonify({"message": "Tag updated", "tags": Video.get_video_tags(video_id)}), 200
        return jsonify({"error": "Failed to update tag"}), 500
    except Exception as e:
        logger.error(f"Error editing video tag: {e}", exc_info=True)
        return jsonify({"error": f"Server error: {str(e)}"}), 500


@app.route('/api/videos/<video_id>/tags', methods=['DELETE'])
@token_required
def delete_video_tag(current_user, video_id):
    """Delete a specific tag from a video"""
    try:
        video = Video.get_video_by_id(video_id)
        if not video:
            return jsonify({"error": "Video not found"}), 404
        if str(video['user_id']) != current_user['user_id']:
            return jsonify({"error": "Access denied"}), 403

        data = request.get_json()
        tag = (data or {}).get('tag', '').strip()
        if not tag:
            return jsonify({"error": "Tag text is required"}), 400

        success = Video.delete_video_tag(video_id, tag)
        if success:
            return jsonify({"message": "Tag deleted", "tags": Video.get_video_tags(video_id)}), 200
        return jsonify({"error": "Failed to delete tag"}), 500
    except Exception as e:
        logger.error(f"Error deleting video tag: {e}", exc_info=True)
        return jsonify({"error": f"Server error: {str(e)}"}), 500


@app.route('/api/videos/<video_id>/category', methods=['PUT'])
@token_required
def update_video_category(current_user, video_id):
    """Update the category for a video"""
    try:
        video = Video.get_video_by_id(video_id)
        if not video:
            return jsonify({"error": "Video not found"}), 404
        if str(video['user_id']) != current_user['user_id']:
            return jsonify({"error": "Access denied"}), 403

        data = request.get_json()
        category = (data or {}).get('category', '').strip()
        if not category:
            return jsonify({"error": "Category is required"}), 400

        success = Video.update_video_category(video_id, category)
        if success:
            return jsonify({"message": "Category updated", "category": category}), 200
        return jsonify({"error": "Failed to update category"}), 500
    except Exception as e:
        logger.error(f"Error updating video category: {e}", exc_info=True)
        return jsonify({"error": f"Server error: {str(e)}"}), 500

# ── End Tag CRUD ────────────────────────────────────────────────────

# ── Entity CRUD ─────────────────────────────────────────────────────

@app.route('/api/videos/<video_id>/entities', methods=['GET'])
@token_required
def get_video_entities(current_user, video_id):
    """Get entities for a video"""
    try:
        video = Video.get_video_by_id(video_id)
        if not video:
            return jsonify({"error": "Video not found"}), 404
        if str(video['user_id']) != current_user['user_id']:
            return jsonify({"error": "Access denied"}), 403
        entities = Entity.get_by_video_id(video_id)
        return jsonify({"video_id": video_id, "entities": entities}), 200
    except Exception as e:
        logger.error(f"Error getting video entities: {e}", exc_info=True)
        return jsonify({"error": f"Server error: {str(e)}"}), 500


@app.route('/api/videos/<video_id>/entities', methods=['POST'])
@token_required
def add_video_entity(current_user, video_id):
    """Add a new entity to a video"""
    try:
        video = Video.get_video_by_id(video_id)
        if not video:
            return jsonify({"error": "Video not found"}), 404
        if str(video['user_id']) != current_user['user_id']:
            return jsonify({"error": "Access denied"}), 403

        data = request.get_json()
        entity_text = (data or {}).get('entity_text', '').strip()
        entity_type = (data or {}).get('entity_type', '').strip().upper()
        if not entity_text or not entity_type:
            return jsonify({"error": "entity_text and entity_type are required"}), 400
        if entity_type not in ('PER', 'ORG', 'LOC'):
            return jsonify({"error": "entity_type must be PER, ORG, or LOC"}), 400
        if len(entity_text) > 255:
            return jsonify({"error": "Entity text too long"}), 400

        success = Entity.add_entity(video_id, current_user['user_id'], entity_text, entity_type)
        if success:
            entities = Entity.get_by_video_id(video_id)
            return jsonify({"message": "Entity added", "entities": entities}), 200
        return jsonify({"error": "Failed to add entity"}), 500
    except Exception as e:
        logger.error(f"Error adding video entity: {e}", exc_info=True)
        return jsonify({"error": f"Server error: {str(e)}"}), 500


@app.route('/api/videos/<video_id>/entities', methods=['PUT'])
@token_required
def edit_video_entity(current_user, video_id):
    """Edit (rename) an entity on a video"""
    try:
        video = Video.get_video_by_id(video_id)
        if not video:
            return jsonify({"error": "Video not found"}), 404
        if str(video['user_id']) != current_user['user_id']:
            return jsonify({"error": "Access denied"}), 403

        data = request.get_json()
        old_text = (data or {}).get('old_text', '').strip()
        old_type = (data or {}).get('old_type', '').strip().upper()
        new_text = (data or {}).get('new_text', '').strip()
        new_type = (data or {}).get('new_type', '').strip().upper()
        if not old_text or not old_type or not new_text or not new_type:
            return jsonify({"error": "old_text, old_type, new_text, new_type are required"}), 400
        if new_type not in ('PER', 'ORG', 'LOC'):
            return jsonify({"error": "new_type must be PER, ORG, or LOC"}), 400
        if len(new_text) > 255:
            return jsonify({"error": "Entity text too long"}), 400

        success = Entity.edit_entity(video_id, old_text, old_type, new_text, new_type)
        if success:
            entities = Entity.get_by_video_id(video_id)
            return jsonify({"message": "Entity updated", "entities": entities}), 200
        return jsonify({"error": "Failed to update entity"}), 500
    except Exception as e:
        logger.error(f"Error editing video entity: {e}", exc_info=True)
        return jsonify({"error": f"Server error: {str(e)}"}), 500


@app.route('/api/videos/<video_id>/entities', methods=['DELETE'])
@token_required
def delete_video_entity(current_user, video_id):
    """Delete a specific entity from a video"""
    try:
        video = Video.get_video_by_id(video_id)
        if not video:
            return jsonify({"error": "Video not found"}), 404
        if str(video['user_id']) != current_user['user_id']:
            return jsonify({"error": "Access denied"}), 403

        data = request.get_json()
        entity_text = (data or {}).get('entity_text', '').strip()
        entity_type = (data or {}).get('entity_type', '').strip().upper()
        if not entity_text or not entity_type:
            return jsonify({"error": "entity_text and entity_type are required"}), 400

        success = Entity.delete_entity(video_id, entity_text, entity_type)
        if success:
            entities = Entity.get_by_video_id(video_id)
            return jsonify({"message": "Entity deleted", "entities": entities}), 200
        return jsonify({"error": "Failed to delete entity"}), 500
    except Exception as e:
        logger.error(f"Error deleting video entity: {e}", exc_info=True)
        return jsonify({"error": f"Server error: {str(e)}"}), 500

# ── End Entity CRUD ─────────────────────────────────────────────────

@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Health check endpoint with system information
    """
    with jobs_lock:
        total_jobs = len(jobs)
        active_jobs = sum(1 for job in jobs.values() if job['status'] in ['queued', 'processing'])
        completed_jobs = sum(1 for job in jobs.values() if job['status'] == 'completed')
        failed_jobs = sum(1 for job in jobs.values() if job['status'] == 'failed')
    
    return jsonify({
        "status": "ok",
        "message": "Backend is running",
        "version": "1.0.0",
        "model": "whisper-tiny",
        "language": "urdu",
        "statistics": {
            "total_jobs": total_jobs,
            "active_jobs": active_jobs,
            "completed_jobs": completed_jobs,
            "failed_jobs": failed_jobs
        },
        "timestamp": datetime.now().isoformat()
    }), 200

@app.route('/api/jobs', methods=['GET'])
def get_all_jobs():
    """
    Get list of all jobs (for debugging/monitoring)
    """
    with jobs_lock:
        jobs_list = [
            {
                "job_id": job_id,
                "status": job['status'],
                "filename": job.get('filename', ''),
                "created_at": job.get('created_at', ''),
                "completed_at": job.get('completed_at', '')
            }
            for job_id, job in jobs.items()
        ]
    
    return jsonify({"jobs": jobs_list, "total": len(jobs_list)}), 200

@app.route('/api/job/<job_id>', methods=['DELETE'])
def delete_job(job_id):
    """
    Delete a job from memory
    """
    with jobs_lock:
        if job_id not in jobs:
            return jsonify({"error": "Job not found"}), 404
        
        del jobs[job_id]
        logger.info(f"[Job {job_id}] Job deleted from memory")
    
    return jsonify({"message": "Job deleted successfully"}), 200

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}", exc_info=True)
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    # Print startup banner
    print("="*60)
    print("   PAK JOURNAL ARCHIVE 77 - BACKEND")
    print("   Version: 1.0.0")
    print("   Model: Whisper Large V3 (Urdu)")
    print("="*60)
    
    # Ensure directories exist
    os.makedirs('uploads', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    # Initialize database
    logger.info("="*60)
    logger.info("Initializing Backend Services...")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info("="*60)
    
    try:
        # Initialize database connection pool
        logger.info("Initializing database connection pool...")
        if init_db_pool():
            if test_db_connection():
                logger.info("[OK] Database connected successfully")
            else:
                logger.warning("[WARN] Database connection test failed - Auth features may not work")
        else:
            logger.warning("[WARN] Database pool initialization failed - Auth features may not work")
        
        # Initialize Whisper model
        initialize_model()
        logger.info("Whisper model initialized successfully")
        logger.info("Backend ready to accept requests")
        logger.info("="*60)
        
        # Start Flask app
        print("\nServer starting on http://0.0.0.0:5000")
        print("Logs available at: logs/system.log")
        print("Ready for Urdu transcription")
        print("Authentication enabled\n")
        
        app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
        
    except Exception as e:
        logger.error(f"Failed to start backend: {str(e)}", exc_info=True)
        print(f"\n[ERROR] Error: {str(e)}")
        print("Please check logs/system.log for details\n")
        exit(1)
    finally:
        # Cleanup database connections on shutdown
        close_db_pool()
