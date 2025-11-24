import whisper
import logging
import os
from .audio_processor import process_audio_for_transcription

logger = logging.getLogger(__name__)

# Load model once at startup to save time
model = None
model_info = {
    "name": "tiny",
    "language": "ur",
    "loaded": False
}

def initialize_model(model_name="tiny"):
    """
    Load the Whisper model on startup
    
    Args:
        model_name: Model size to load (tiny, base, small, medium, large)
    """
    global model, model_info
    
    try:
        logger.info(f"Loading Whisper '{model_name}' model...")
        logger.info("This may take a few moments on first run...")
        
        # Load the model
        model = whisper.load_model(model_name)
        
        model_info = {
            "name": model_name,
            "language": "ur",
            "loaded": True
        }
        
        logger.info(f"✓ Whisper '{model_name}' model loaded successfully")
        logger.info(f"✓ Model configured for Urdu language")
        return True
        
    except Exception as e:
        logger.error(f"✗ Failed to load Whisper model: {str(e)}")
        model_info["loaded"] = False
        raise e

def get_model_info():
    """Return information about the loaded model"""
    return model_info

def transcribe_video(file_path, job_id):
    """
    Transcribe video/audio file to Urdu text with full audio preprocessing.
    
    This function:
    1. Processes the audio through the optimization pipeline (audio_processor.py)
    2. Transcribes the clean, optimized audio with Whisper
    
    Args:
        file_path: Path to the uploaded video/audio file
        job_id: Unique identifier for the job
    
    Returns:
        dict: Extended Whisper result with:
            - text: Full transcription
            - segments: Timestamped segments
            - language: Detected language
            - audio_metadata: Processing stats
    """
    if model is None:
        error_msg = "Whisper model not initialized"
        logger.error(f"[Job {job_id}] {error_msg}")
        raise RuntimeError(error_msg)
    
    if not os.path.exists(file_path):
        error_msg = f"File not found: {file_path}"
        logger.error(f"[Job {job_id}] {error_msg}")
        raise FileNotFoundError(error_msg)
    
    try:
        logger.info(f"[Job {job_id}] Starting transcription pipeline")
        logger.info(f"[Job {job_id}] Input file: {os.path.basename(file_path)}")
        
        # ========================================
        # STEP 1: AUDIO PREPROCESSING
        # ========================================
        logger.info(f"[Job {job_id}] Phase 1: Audio preprocessing")
        
        # Create job-specific output directory
        job_audio_dir = os.path.join("processed_audio", f"job_{job_id}")
        
        # Process audio through optimization pipeline
        audio_result = process_audio_for_transcription(
            input_path=file_path,
            output_dir=job_audio_dir,
            enable_noise_reduction=True,  # Always enable for best quality
            enable_chunking=False  # Whisper handles long files well with clean audio
        )
        
        processed_audio_path = audio_result['clean_audio_path']
        audio_metadata = audio_result['metadata']
        
        logger.info(f"[Job {job_id}] ✓ Audio preprocessed successfully")
        logger.info(f"[Job {job_id}]   Duration: {audio_metadata['duration_seconds']:.1f}s")
        logger.info(f"[Job {job_id}]   Sample rate: {audio_metadata['sample_rate']}Hz")
        logger.info(f"[Job {job_id}]   Noise reduction: {audio_metadata['noise_reduction_applied']}")
        
        # ========================================
        # STEP 2: WHISPER TRANSCRIPTION
        # ========================================
        logger.info(f"[Job {job_id}] Phase 2: Whisper transcription")
        logger.info(f"[Job {job_id}] Language: Urdu (ur)")
        logger.info(f"[Job {job_id}] Model: {model_info.get('name', 'unknown')}")
        
        # Transcribe the PROCESSED audio (not the original file)
        result = model.transcribe(
            processed_audio_path,  # Use processed audio, not original
            language="ur",          # Force Urdu
            fp16=False,             # Use FP32 for CPU compatibility
            verbose=False,          # Disable verbose output to logs
            task="transcribe",      # Transcribe (not translate)
            temperature=0.0,        # Use greedy decoding for consistency
            compression_ratio_threshold=2.4,
            logprob_threshold=-1.0,
            no_speech_threshold=0.6
        )
        
        # ========================================
        # STEP 3: RESULTS & CLEANUP
        # ========================================
        # Log transcription details
        text_length = len(result.get('text', ''))
        num_segments = len(result.get('segments', []))
        detected_language = result.get('language', 'unknown')
        
        logger.info(f"[Job {job_id}] ✓ Transcription completed successfully")
        logger.info(f"[Job {job_id}] Detected language: {detected_language}")
        logger.info(f"[Job {job_id}] Text length: {text_length} characters")
        logger.info(f"[Job {job_id}] Number of segments: {num_segments}")
        
        if text_length == 0:
            logger.warning(f"[Job {job_id}] Warning: Transcript is empty")
        
        # Add audio processing metadata to result
        result['audio_metadata'] = audio_metadata
        result['processed_audio_path'] = processed_audio_path
        
        return result
        
    except FileNotFoundError:
        raise
        
    except Exception as e:
        logger.error(f"[Job {job_id}] ✗ Transcription pipeline failed: {str(e)}")
        logger.error(f"[Job {job_id}] File: {file_path}")
        logger.error(f"[Job {job_id}] Error type: {type(e).__name__}")
        raise e
