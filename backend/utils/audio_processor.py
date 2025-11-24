import os
import logging
import numpy as np
import ffmpeg
from pydub import AudioSegment
from pydub.silence import detect_silence
import noisereduce as nr
from scipy.io import wavfile
from scipy.signal import butter, sosfilt

logger = logging.getLogger(__name__)

class AudioProcessor:
    """
    Optimized audio processor for Whisper transcription.
    Implements all best practices from AUDIO_PROCESSING_README.md
    """
    
    def __init__(self, base_output_dir="processed_audio"):
        self.base_output_dir = base_output_dir
        if not os.path.exists(base_output_dir):
            os.makedirs(base_output_dir)
        
        # Optimal settings for Whisper
        self.TARGET_SAMPLE_RATE = 16000  # 16kHz
        self.TARGET_CHANNELS = 1         # Mono
        self.TARGET_DBFS = -3.0          # Peak normalization
        self.OPTIMAL_CHUNK_LENGTH = 28000  # 28 seconds in ms (under 30s limit)
        self.OVERLAP_DURATION = 2000     # 2 seconds overlap in ms
        self.MIN_SILENCE_LEN = 500       # 500ms minimum silence
        self.SILENCE_THRESH = -40        # Silence threshold in dBFS

    def extract_audio(self, video_path):
        """
        Extracts audio from video and converts it to Whisper-optimized format:
        16kHz, Mono, PCM WAV.
        
        Args:
            video_path: Path to the input video file
            
        Returns:
            str: Path to the extracted raw audio file
        """
        try:
            filename = os.path.splitext(os.path.basename(video_path))[0]
            output_path = os.path.join(self.base_output_dir, f"{filename}_raw.wav")
            
            logger.info(f"Extracting audio from {os.path.basename(video_path)}...")
            
            # FFmpeg extraction with optimal settings
            (
                ffmpeg
                .input(video_path)
                .output(
                    output_path,
                    acodec='pcm_s16le',  # PCM 16-bit
                    ac=self.TARGET_CHANNELS,  # Mono
                    ar=str(self.TARGET_SAMPLE_RATE),  # 16kHz
                    vn=None,  # No video
                    loglevel='error'
                )
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
            
            logger.info(f"✓ Audio extracted: {os.path.basename(output_path)}")
            return output_path
            
        except ffmpeg.Error as e:
            error_msg = e.stderr.decode('utf8') if e.stderr else str(e)
            logger.error(f"✗ FFmpeg extraction failed: {error_msg}")
            raise Exception(f"Failed to extract audio: {error_msg}")

    def apply_highpass_filter(self, data, sample_rate, cutoff=100, order=5):
        """
        Apply high-pass filter to remove low-frequency rumble.
        
        Args:
            data: Audio data (numpy array)
            sample_rate: Sample rate in Hz
            cutoff: Cutoff frequency in Hz (default 100Hz)
            order: Filter order
            
        Returns:
            numpy.ndarray: Filtered audio data
        """
        nyquist = 0.5 * sample_rate
        normal_cutoff = cutoff / nyquist
        sos = butter(order, normal_cutoff, btype='high', analog=False, output='sos')
        filtered_data = sosfilt(sos, data)
        return filtered_data.astype(data.dtype)

    def reduce_noise(self, audio_path):
        """
        Applies spectral gating noise reduction to the audio file.
        Also applies high-pass filter to remove low-frequency noise.
        
        Args:
            audio_path: Path to the raw audio file
            
        Returns:
            str: Path to the noise-reduced audio file
        """
        try:
            logger.info(f"Starting noise reduction for {os.path.basename(audio_path)}...")
            
            # Load audio data
            rate, data = wavfile.read(audio_path)
            
            # Convert to float32 for processing
            if data.dtype == np.int16:
                data = data.astype(np.float32) / 32768.0
            elif data.dtype == np.int32:
                data = data.astype(np.float32) / 2147483648.0
            
            # Step 1: Apply high-pass filter (remove rumble below 100Hz)
            logger.info("Applying high-pass filter (100Hz cutoff)...")
            data = self.apply_highpass_filter(data, rate, cutoff=100)
            
            # Step 2: Spectral gating noise reduction
            logger.info("Applying spectral gating noise reduction...")
            reduced_noise = nr.reduce_noise(
                y=data,
                sr=rate,
                stationary=True,  # Assumes constant background noise
                prop_decrease=0.75  # Remove 75% of detected noise profile
            )
            
            # Convert back to int16
            reduced_noise = np.clip(reduced_noise, -1.0, 1.0)
            reduced_noise = (reduced_noise * 32767).astype(np.int16)
            
            filename = os.path.splitext(os.path.basename(audio_path))[0].replace('_raw', '')
            output_path = os.path.join(self.base_output_dir, f"{filename}_clean.wav")
            
            wavfile.write(output_path, rate, reduced_noise)
            
            logger.info(f"✓ Noise reduction completed: {os.path.basename(output_path)}")
            return output_path
            
        except Exception as e:
            logger.error(f"✗ Noise reduction failed: {str(e)}")
            logger.warning("Falling back to original audio without noise reduction")
            return audio_path

    def normalize_audio(self, audio_path, target_dBFS=-3.0):
        """
        Normalizes audio volume to a target dBFS using peak normalization.
        
        Args:
            audio_path: Path to the audio file
            target_dBFS: Target dBFS level (default -3.0)
            
        Returns:
            str: Path to the normalized audio file
        """
        try:
            logger.info(f"Normalizing audio to {target_dBFS}dBFS...")
            audio = AudioSegment.from_wav(audio_path)
            
            change_in_dBFS = target_dBFS - audio.dBFS
            normalized_audio = audio.apply_gain(change_in_dBFS)
            
            filename = os.path.splitext(os.path.basename(audio_path))[0].replace('_clean', '')
            output_path = os.path.join(self.base_output_dir, f"{filename}_final.wav")
            
            normalized_audio.export(output_path, format="wav")
            
            logger.info(f"✓ Audio normalized: {os.path.basename(output_path)}")
            return output_path
            
        except Exception as e:
            logger.error(f"✗ Normalization failed: {str(e)}")
            return audio_path

    def split_with_overlap(self, audio, chunk_length_ms, overlap_ms):
        """
        Split audio into overlapping chunks (fallback for continuous speech).
        
        Args:
            audio: AudioSegment object
            chunk_length_ms: Target chunk length in milliseconds
            overlap_ms: Overlap duration in milliseconds
            
        Returns:
            list: List of AudioSegment chunks
        """
        chunks = []
        start = 0
        audio_length = len(audio)
        
        while start < audio_length:
            end = min(start + chunk_length_ms, audio_length)
            chunk = audio[start:end]
            chunks.append(chunk)
            
            # Move forward by chunk_length minus overlap
            start += (chunk_length_ms - overlap_ms)
            
            # If we're close to the end, just take the rest
            if start + overlap_ms >= audio_length:
                break
        
        return chunks

    def split_audio_smart(self, audio_path):
        """
        Intelligently splits audio into optimal chunks for Whisper processing.
        
        Strategy:
        1. Primary: Split on silence (natural pauses) targeting 25-28s chunks
        2. Fallback: Use overlapping windows with 2s overlap if no silence found
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            list: List of paths to chunk files
        """
        try:
            logger.info(f"Analyzing audio for optimal chunking...")
            audio = AudioSegment.from_wav(audio_path)
            audio_length_ms = len(audio)
            
            # If audio is shorter than optimal chunk length, no need to split
            if audio_length_ms <= self.OPTIMAL_CHUNK_LENGTH:
                logger.info(f"Audio is {audio_length_ms/1000:.1f}s, no chunking needed")
                return [audio_path]
            
            filename_base = os.path.splitext(os.path.basename(audio_path))[0].replace('_final', '')
            chunk_dir = os.path.join(self.base_output_dir, f"{filename_base}_chunks")
            if not os.path.exists(chunk_dir):
                os.makedirs(chunk_dir)
            
            chunk_paths = []
            
            # Detect silence periods
            silence_ranges = detect_silence(
                audio,
                min_silence_len=self.MIN_SILENCE_LEN,
                silence_thresh=self.SILENCE_THRESH,
                seek_step=100
            )
            
            logger.info(f"Found {len(silence_ranges)} silence periods")
            
            # Strategy 1: Silence-based splitting (preferred)
            if len(silence_ranges) > 0:
                logger.info("Using silence-based chunking (optimal method)")
                
                chunks = []
                last_cut = 0
                current_chunk_start = 0
                
                for silence_start, silence_end in silence_ranges:
                    # Check if we've reached optimal chunk length
                    potential_length = silence_start - current_chunk_start
                    
                    if potential_length >= self.OPTIMAL_CHUNK_LENGTH * 0.9:  # 90% of target
                        # Cut at this silence
                        cut_point = (silence_start + silence_end) // 2  # Middle of silence
                        chunk = audio[current_chunk_start:cut_point]
                        chunks.append(chunk)
                        current_chunk_start = cut_point
                
                # Add the last chunk
                if current_chunk_start < audio_length_ms:
                    chunks.append(audio[current_chunk_start:])
                
            else:
                # Strategy 2: Overlapping windows (fallback)
                logger.info("No silence detected, using overlapping windows (fallback method)")
                chunks = self.split_with_overlap(
                    audio,
                    self.OPTIMAL_CHUNK_LENGTH,
                    self.OVERLAP_DURATION
                )
            
            # Export chunks
            for i, chunk in enumerate(chunks):
                chunk_name = f"chunk_{i:03d}.wav"
                chunk_path = os.path.join(chunk_dir, chunk_name)
                chunk.export(chunk_path, format="wav")
                chunk_paths.append(chunk_path)
                logger.info(f"  Created chunk {i+1}/{len(chunks)}: {len(chunk)/1000:.1f}s")
            
            logger.info(f"✓ Audio split into {len(chunk_paths)} optimized chunks")
            return chunk_paths
            
        except Exception as e:
            logger.error(f"✗ Chunking failed: {str(e)}")
            logger.warning("Falling back to single file processing")
            return [audio_path]


def process_audio_for_transcription(
    input_path,
    output_dir="processed_audio",
    enable_noise_reduction=True,
    enable_chunking=False
):
    """
    Main entry point: Complete audio processing pipeline for Whisper.
    
    Implements all optimizations from AUDIO_PROCESSING_README.md:
    - 16kHz mono conversion
    - High-pass filtering
    - Spectral gating noise reduction
    - Peak normalization to -3dB
    - Smart chunking (silence-based or overlapping)
    
    Args:
        input_path: Path to input video/audio file
        output_dir: Directory for processed audio output
        enable_noise_reduction: Whether to apply noise reduction (default True)
        enable_chunking: Whether to split into chunks (default False)
        
    Returns:
        dict: {
            'clean_audio_path': Path to processed audio file,
            'chunks': List of chunk paths (empty if chunking disabled),
            'metadata': Processing metadata
        }
    """
    processor = AudioProcessor(output_dir)
    
    logger.info("="*60)
    logger.info("AUDIO PROCESSING PIPELINE STARTED")
    logger.info(f"Input: {os.path.basename(input_path)}")
    logger.info("="*60)
    
    # Step 1: Extract audio (16kHz, Mono, WAV)
    logger.info("Step 1/4: Extracting audio...")
    raw_audio = processor.extract_audio(input_path)
    
    # Step 2: Noise Reduction (Optional but recommended)
    if enable_noise_reduction:
        logger.info("Step 2/4: Reducing noise...")
        clean_audio = processor.reduce_noise(raw_audio)
    else:
        logger.info("Step 2/4: Noise reduction skipped")
        clean_audio = raw_audio
    
    # Step 3: Normalize volume
    logger.info("Step 3/4: Normalizing volume...")
    final_audio = processor.normalize_audio(clean_audio)
    
    # Step 4: Chunking (Optional)
    chunks = []
    if enable_chunking:
        logger.info("Step 4/4: Chunking audio...")
        chunks = processor.split_audio_smart(final_audio)
    else:
        logger.info("Step 4/4: Chunking disabled")
    
    # Calculate metadata
    audio = AudioSegment.from_wav(final_audio)
    duration_seconds = len(audio) / 1000.0
    
    metadata = {
        'duration_seconds': duration_seconds,
        'sample_rate': processor.TARGET_SAMPLE_RATE,
        'channels': processor.TARGET_CHANNELS,
        'num_chunks': len(chunks),
        'noise_reduction_applied': enable_noise_reduction
    }
    
    logger.info("="*60)
    logger.info("AUDIO PROCESSING COMPLETED")
    logger.info(f"Duration: {duration_seconds:.1f}s")
    logger.info(f"Output: {os.path.basename(final_audio)}")
    if chunks:
        logger.info(f"Chunks: {len(chunks)} files")
    logger.info("="*60)
    
    return {
        'clean_audio_path': final_audio,
        'chunks': chunks,
        'metadata': metadata
    }
