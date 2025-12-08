import torch
import gc
from transformers import WhisperProcessor, WhisperForConditionalGeneration
import logging
import os
import soundfile as sf
import numpy as np
from .audio_processor import process_audio_for_transcription

logger = logging.getLogger(__name__)

# Load model once at startup to save time
model = None
processor = None
device = None
model_info = {
    "name": "openai/whisper-large-v3",
    "language": "ur",
    "loaded": False
}

def initialize_model(model_name="openai/whisper-large-v3"):
    """
    Load the Whisper model from HuggingFace on startup with memory cleanup
    
    Args:
        model_name: HuggingFace model ID to load
    """
    global model, processor, device, model_info
    
    try:
        logger.info(f"Loading Whisper model '{model_name}' from HuggingFace...")
        logger.info("This may take a few moments on first run...")
        
        # Clear GPU memory before loading
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            logger.info("GPU memory cleared before model loading")
        
        # Determine device
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {device}")
        logger.info(f"Using dtype: torch.float16")
        
        # Load the processor
        processor = WhisperProcessor.from_pretrained(model_name)
        logger.info("✓ Processor loaded")
        
        # Load the model with float16
        model = WhisperForConditionalGeneration.from_pretrained(
            model_name,
            torch_dtype=torch.float16
        ).to(device)
        logger.info("✓ Model loaded and moved to device")
        
        model_info = {
            "name": model_name,
            "language": "ur",
            "device": device,
            "dtype": "torch.float16",
            "loaded": True
        }
        
        logger.info(f"✓ Whisper model '{model_name}' loaded successfully")
        logger.info(f"✓ Model configured for Urdu language")
        return True
        
    except Exception as e:
        logger.error(f"✗ Failed to load Whisper model: {str(e)}")
        model_info["loaded"] = False
        raise e

def get_model_info():
    """Return information about the loaded model"""
    return model_info

def transcribe_long_audio(wav_path, job_id, chunk_seconds=30):
    """
    Transcribe long audio files using chunking approach with memory management.
    
    Args:
        wav_path: Path to the audio file (must be 16kHz WAV)
        job_id: Job identifier for logging
        chunk_seconds: Length of each chunk in seconds
    
    Returns:
        dict: Result with full text and segments
    """
    global model, processor, device
    
    LANGUAGE = "ur"
    TASK = "transcribe"
    
    # Read audio file
    audio, sr = sf.read(wav_path)
    logger.info(f"[Job {job_id}] Audio loaded: {len(audio)} samples at {sr}Hz")
    
    # Ensure 16kHz sample rate
    if sr != 16000:
        logger.warning(f"[Job {job_id}] Audio is {sr}Hz, expected 16kHz. Results may vary.")
    
    # Calculate samples per chunk
    step = chunk_seconds * sr
    full_text = ""
    segments = []
    
    num_chunks = (len(audio) + step - 1) // step
    logger.info(f"[Job {job_id}] Processing {num_chunks} chunks of {chunk_seconds}s each")
    
    for chunk_idx, i in enumerate(range(0, len(audio), step), 1):
        chunk = audio[i:i+step]
        start_time = i / sr
        
        logger.info(f"[Job {job_id}] Processing chunk {chunk_idx}/{num_chunks} (at {start_time:.1f}s)")
        
        # Prepare inputs
        inputs = processor(chunk, sampling_rate=16000, return_tensors="pt").to(device)
        inputs["input_features"] = inputs["input_features"].to(model.dtype)
        
        # Generate transcription
        with torch.no_grad():
            predicted_ids = model.generate(
                inputs["input_features"],
                task=TASK,
                language=LANGUAGE,
                max_new_tokens=200,
                num_beams=2
            )
        
        # Decode text
        text = processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]
        full_text += text + " "
        
        # Create segment
        end_time = min((i + step) / sr, len(audio) / sr)
        segments.append({
            "text": text,
            "start": start_time,
            "end": end_time
        })
        
        # Clear GPU cache after each chunk
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    
    logger.info(f"[Job {job_id}] ✓ All {num_chunks} chunks processed")
    
    return {
        "text": full_text.strip(),
        "segments": segments,
        "language": LANGUAGE
    }

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
    if model is None or processor is None:
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
        
   
        # STEP 1: AUDIO PREPROCESSING
      
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
        
        logger.info(f"[Job {job_id}]   Audio preprocessed successfully")
        logger.info(f"[Job {job_id}]   Duration: {audio_metadata['duration_seconds']:.1f}s")
        logger.info(f"[Job {job_id}]   Sample rate: {audio_metadata['sample_rate']}Hz")
        logger.info(f"[Job {job_id}]   Noise reduction: {audio_metadata['noise_reduction_applied']}")
        
       
        # STEP 2: WHISPER TRANSCRIPTION
       
        logger.info(f"[Job {job_id}] Phase 2: Whisper transcription")
        logger.info(f"[Job {job_id}] Language: Urdu (ur)")
        logger.info(f"[Job {job_id}] Model: {model_info.get('name', 'unknown')}")
        logger.info(f"[Job {job_id}] Device: {model_info.get('device', 'unknown')}")
        
        # Clear GPU memory before transcription
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            logger.info(f"[Job {job_id}] GPU memory cleared before transcription")
        
        # Transcribe using chunked approach for long audio
        result = transcribe_long_audio(processed_audio_path, job_id, chunk_seconds=30)
        
        
        # STEP 3: RESULTS & CLEANUP
        
        # Log transcription details
        text_length = len(result.get('text', ''))
        num_segments = len(result.get('segments', []))
        detected_language = result.get('language', 'unknown')
        
        logger.info(f"[Job {job_id}] Transcription completed successfully")
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
        logger.error(f"[Job {job_id}] Transcription pipeline failed: {str(e)}")
        logger.error(f"[Job {job_id}] File: {file_path}")
        logger.error(f"[Job {job_id}] Error type: {type(e).__name__}")
        raise e
