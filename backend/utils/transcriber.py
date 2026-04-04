import torch
import gc
from transformers import WhisperProcessor, WhisperForConditionalGeneration
import logging
import os
import soundfile as sf
import numpy as np
from .audio_processor import process_audio_for_transcription

logger = logging.getLogger(__name__)

# Global model objects
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
    Load the Whisper model manually for optimized batch processing.
    """
    global model, processor, device, model_info
    
    try:
        logger.info(f"Loading Whisper model '{model_name}'...")
        
        # Clear GPU memory
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        device = "cuda" if torch.cuda.is_available() else "cpu"
        # Use float16 for GPU, float32 for CPU
        torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        
        logger.info(f"Using device: {device}")
        logger.info(f"Using dtype: {torch_dtype}")
        
        processor = WhisperProcessor.from_pretrained(model_name)
        model = WhisperForConditionalGeneration.from_pretrained(
            model_name,
            torch_dtype=torch_dtype
        ).to(device)
        
        # Optimize model for inference
        model.eval()
        
        model_info = {
            "name": model_name,
            "language": "ur",
            "device": device,
            "dtype": str(torch_dtype),
            "loaded": True
        }
        
        logger.info(f"[OK] Whisper model loaded successfully")
        return True
        
    except Exception as e:
        logger.error(f"[FAIL] Failed to load Whisper model: {str(e)}")
        model_info["loaded"] = False
        raise e

def unload_model():
    """Free Whisper model from GPU to reclaim VRAM."""
    global model, processor, model_info
    if model is not None:
        del model
        model = None
    if processor is not None:
        del processor
        processor = None
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    model_info["loaded"] = False
    logger.info("Whisper model unloaded from VRAM")

def get_model_info():
    return model_info

def smart_chunk_audio(audio, sr=16000, min_duration=15, max_duration=30):
    """
    Split audio into chunks at silence points using RMS energy detection.
    This prevents cutting words in half by finding the quietest spot.
    """
    chunks = []
    timestamps = []
    
    total_samples = len(audio)
    current_pos = 0
    
    min_samples = int(min_duration * sr)
    max_samples = int(max_duration * sr)
    
    # Frame size for energy calculation (50ms)
    frame_length = int(0.05 * sr)
    
    while current_pos < total_samples:
        # If remaining audio is less than max_duration, just take it all
        if total_samples - current_pos <= max_samples:
            chunk = audio[current_pos:]
            chunks.append(chunk)
            timestamps.append(current_pos / sr)
            break
            
        # Define search window for silence (between 15s and 30s)
        search_start = current_pos + min_samples
        search_end = current_pos + max_samples
        
        # Get the audio segment where we want to cut
        search_segment = audio[search_start:search_end]
        
        # Calculate RMS energy in frames to find true silence
        # Instead of checking every sample, we check 50ms windows
        min_energy = float('inf')
        best_split_offset = 0
        
        # Iterate through the search segment in steps of frame_length
        for i in range(0, len(search_segment) - frame_length, frame_length):
            frame = search_segment[i:i+frame_length]
            energy = np.sqrt(np.mean(frame**2))
            
            if energy < min_energy:
                min_energy = energy
                # Cut in the middle of the quietest frame
                best_split_offset = i + (frame_length // 2)
        
        # If we didn't find a good frame (segment too short?), fallback to middle
        if min_energy == float('inf'):
            best_split_offset = len(search_segment) // 2

        split_point = search_start + best_split_offset
        
        # Create chunk
        chunk = audio[current_pos:split_point]
        chunks.append(chunk)
        timestamps.append(current_pos / sr)
        
        current_pos = split_point
        
    return chunks, timestamps

def _dedup_segment_text(text):
    """Remove repeated consecutive words/phrases within a single segment."""
    words = text.split()
    if len(words) < 2:
        return text

    # Pass 1: Remove consecutive duplicate words (e.g., "کہ کہ کہ" → "کہ")
    deduped = [words[0]]
    for w in words[1:]:
        if w != deduped[-1]:
            deduped.append(w)
    words = deduped

    # Pass 2: Remove repeated phrases (2-6 word n-grams repeated consecutively)
    for n in range(6, 1, -1):
        if len(words) < n * 2:
            continue
        cleaned = []
        i = 0
        while i < len(words):
            if i + n * 2 <= len(words) and words[i:i+n] == words[i+n:i+n*2]:
                # Found a repeated n-gram, keep one copy and skip all repeats
                cleaned.extend(words[i:i+n])
                i += n
                while i + n <= len(words) and words[i:i+n] == cleaned[-n:]:
                    i += n
            else:
                cleaned.append(words[i])
                i += 1
        words = cleaned

    return " ".join(words)


def _dedup_consecutive_segments(segments):
    """Remove overlapping text between consecutive segments."""
    if len(segments) < 2:
        return segments

    cleaned = [segments[0].copy()]
    cleaned[0]["text"] = _dedup_segment_text(cleaned[0]["text"])

    for seg in segments[1:]:
        prev_words = cleaned[-1]["text"].split()
        cur_words = seg["text"].split()

        if not cur_words:
            continue

        # Find longest suffix of prev that matches prefix of cur (up to 15 words)
        max_check = min(15, len(prev_words), len(cur_words))
        overlap = 0
        for length in range(1, max_check + 1):
            if prev_words[-length:] == cur_words[:length]:
                overlap = length

        new_seg = seg.copy()
        if overlap > 0:
            new_seg["text"] = " ".join(cur_words[overlap:])

        # Also dedup within the segment
        new_seg["text"] = _dedup_segment_text(new_seg["text"])

        if new_seg["text"].strip():
            cleaned.append(new_seg)

    return cleaned


def transcribe_video(file_path, job_id, update_status_callback=None):
    """
    Transcribe using manual batch processing with smart chunking.
    """
    if model is None:
        logger.info(f"[Job {job_id}] Whisper model not loaded, reinitializing...")
        initialize_model()
        
    try:
        logger.info(f"[Job {job_id}] Starting optimized transcription (Smart Batch Mode)")
        
        # 1. Preprocess Audio
        if update_status_callback:
            update_status_callback(step="Preprocessing audio...")
            
        job_audio_dir = os.path.join("processed_audio", f"job_{job_id}")
        audio_result = process_audio_for_transcription(
            input_path=file_path,
            output_dir=job_audio_dir,
            enable_noise_reduction=True
        )
        wav_path = audio_result['clean_audio_path']
        
        # 2. Load Audio
        audio, sr = sf.read(wav_path)
        logger.info(f"[Job {job_id}] Audio loaded: {len(audio)/sr:.1f}s")
        
        # 3. Prepare Batches with Smart Chunking
        chunks, timestamps = smart_chunk_audio(audio, sr)
        
        # Pad chunks to 30s for Whisper
        CHUNK_SAMPLES = 30 * 16000
        padded_chunks = []
        
        for chunk in chunks:
            if len(chunk) < CHUNK_SAMPLES:
                chunk = np.pad(chunk, (0, CHUNK_SAMPLES - len(chunk)))
            elif len(chunk) > CHUNK_SAMPLES:
                # Should not happen with our logic, but just in case
                chunk = chunk[:CHUNK_SAMPLES]
            padded_chunks.append(chunk)
            
        logger.info(f"[Job {job_id}] Processing {len(padded_chunks)} chunks...")
        
        full_text = ""
        segments = []
        
        # 4. Run Inference in Batches
        BATCH_SIZE = 4 
        total_batches = (len(padded_chunks) + BATCH_SIZE - 1) // BATCH_SIZE
        
        for i in range(0, len(padded_chunks), BATCH_SIZE):
            current_batch = i//BATCH_SIZE + 1
            logger.info(f"[Job {job_id}] Processing batch {current_batch}/{total_batches}")
            
            if update_status_callback:
                progress_percent = int((current_batch / total_batches) * 100)
                update_status_callback(step=f"Transcribing batch {current_batch}/{total_batches} ({progress_percent}%)")
            
            batch_chunks = padded_chunks[i:i + BATCH_SIZE]
            batch_start_times = timestamps[i:i + BATCH_SIZE]
            
            # Prepare inputs
            input_features = processor(
                batch_chunks, 
                sampling_rate=16000, 
                return_tensors="pt"
            ).input_features.to(device)
            
            if model.dtype == torch.float16:
                input_features = input_features.half()
            
            # Generate
            # Force Urdu language tokens to be absolutely sure
            forced_decoder_ids = processor.get_decoder_prompt_ids(language="ur", task="transcribe")
            
            with torch.no_grad():
                predicted_ids = model.generate(
                    input_features,
                    forced_decoder_ids=forced_decoder_ids,
                    max_new_tokens=440,
                    num_beams=2,          # Use beam search for better accuracy
                    repetition_penalty=1.2 # Slightly increased to prevent loops
                )
            
            # Decode
            transcriptions = processor.batch_decode(predicted_ids, skip_special_tokens=True)
            
            # Collect results
            for j, text in enumerate(transcriptions):
                if text.strip():
                    start_time = batch_start_times[j]
                    # Calculate end time based on next chunk start or audio length
                    if j < len(batch_start_times) - 1:
                        end_time = batch_start_times[j+1]
                    elif i + j + 1 < len(timestamps):
                        end_time = timestamps[i+j+1]
                    else:
                        end_time = len(audio)/16000
                    
                    full_text += text + " "
                    segments.append({
                        "text": text.strip(),
                        "start": start_time,
                        "end": end_time
                    })
            
            # Clear GPU cache
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                
        logger.info(f"[Job {job_id}] Transcription complete. Length: {len(full_text)} chars")

        # Post-process: remove repeated words/phrases and cross-segment overlaps
        segments = _dedup_consecutive_segments(segments)
        full_text = " ".join(seg["text"] for seg in segments)
        logger.info(f"[Job {job_id}] After dedup: {len(full_text)} chars, {len(segments)} segments")
        
        return {
            "text": full_text.strip(),
            "segments": segments,
            "language": "ur",
            "audio_metadata": audio_result['metadata'],
            "processed_audio_path": wav_path
        }

    except Exception as e:
        logger.error(f"[Job {job_id}] Transcription failed: {str(e)}")
        raise e
