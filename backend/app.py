import os
import uuid
import threading
import logging
import time
import json
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from utils.transcriber import initialize_model, transcribe_video
from database.db_config import init_db_pool, test_db_connection, close_db_pool
from database.video_models import Video, Transcription
from routes.auth import auth_bp, token_required

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# Register authentication blueprint
app.register_blueprint(auth_bp, url_prefix='/api/auth')

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
    """
    try:
        current_time = time.time()
        for filename in os.listdir('uploads'):
            filepath = os.path.join('uploads', filename)
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
        update_job_status(job_id, step='Transcribing to Urdu... (this may take a few minutes)')
        logger.info(f"[Job {job_id}] Starting Whisper transcription with preprocessed audio...")
        
        result = transcribe_video(file_path, job_id)
        
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
                        "model": "whisper-tiny",
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
                    model_used="whisper-tiny",
                    segments=json.dumps(result.get('segments', [])),
                    audio_metadata=json.dumps(result.get('audio_metadata', {})),
                    processing_time=processing_time
                )
                
                logger.info(f"[Job {job_id}] Saved to database - Video: {video_id}, Transcription: {transcription_id}")
            except Exception as db_error:
                logger.error(f"[Job {job_id}] Database save failed: {db_error}")
        
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
        
        # Cleanup: Remove uploaded file and processed audio after successful processing
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"[Job {job_id}] Cleaned up uploaded file: {filename}")
            
            # Cleanup processed audio directory for this job
            job_audio_dir = os.path.join("processed_audio", f"job_{job_id}")
            if os.path.exists(job_audio_dir):
                import shutil
                shutil.rmtree(job_audio_dir)
                logger.info(f"[Job {job_id}] Cleaned up processed audio directory")
        except Exception as e:
            logger.warning(f"[Job {job_id}] Failed to cleanup file: {str(e)}")
        
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
        
        file_size = os.path.getsize(save_path)
        logger.info(f"[Job {job_id}] File uploaded: {file.filename} ({file_size / (1024*1024):.2f} MB)")
        
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
    print("   Model: Whisper Tiny (Urdu)")
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
                logger.info("✓ Database connected successfully")
            else:
                logger.warning("⚠ Database connection test failed - Auth features may not work")
        else:
            logger.warning("⚠ Database pool initialization failed - Auth features may not work")
        
        # Initialize Whisper model
        initialize_model()
        logger.info("Whisper model initialized successfully")
        logger.info("Backend ready to accept requests")
        logger.info("="*60)
        
        # Start Flask app
        print("\n🚀 Server starting on http://0.0.0.0:5000")
        print("📝 Logs available at: logs/system.log")
        print("🎤 Ready for Urdu transcription")
        print("🔐 Authentication enabled\n")
        
        app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
        
    except Exception as e:
        logger.error(f"Failed to start backend: {str(e)}", exc_info=True)
        print(f"\n❌ Error: {str(e)}")
        print("Please check logs/system.log for details\n")
        exit(1)
    finally:
        # Cleanup database connections on shutdown
        close_db_pool()
