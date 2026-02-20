# utils/audio_processor.py
import os
import subprocess
import numpy as np
import logging
from typing import Dict, List, Optional
from pydub import AudioSegment
from pydub.silence import detect_silence, split_on_silence

logger = logging.getLogger(__name__)

class AudioProcessor:
    def __init__(self):
        self.supported_formats = ['.wav', '.mp3', '.m4a', '.webm']
    
    def extract_audio(self, video_path: str, output_path: Optional[str] = None) -> str:
        """Extract audio from video file"""
        try:
            if not output_path:
                output_path = video_path.replace('.mp4', '.wav').replace('.webm', '.wav')
            
            logger.info(f"Extracting audio: {video_path} -> {output_path}")
            
            cmd = [
                'ffmpeg', '-i', video_path,
                '-acodec', 'pcm_s16le',
                '-ar', '16000',
                '-ac', '1',
                '-y', output_path
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            
            logger.info(f"Audio extracted successfully: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Audio extraction error: {str(e)}")
            raise
    
    def get_audio_metadata(self, audio_path: str) -> Dict:
        """Get audio file metadata"""
        try:
            audio = AudioSegment.from_file(audio_path)
            
            metadata = {
                'duration': len(audio) / 1000.0,  # Convert to seconds
                'channels': audio.channels,
                'sample_width': audio.sample_width,
                'frame_rate': audio.frame_rate,
                'file_size': os.path.getsize(audio_path)
            }
            
            return metadata
            
        except Exception as e:
            logger.error(f"Audio metadata extraction error: {str(e)}")
            raise
    
    def detect_silence_segments(self, audio_path: str, 
                              silence_thresh: int = -40, 
                              min_silence_len: int = 500) -> List[Dict]:
        """Detect silence segments in audio"""
        try:
            audio = AudioSegment.from_file(audio_path)
            silence_segments = detect_silence(
                audio, 
                min_silence_len=min_silence_len, 
                silence_thresh=silence_thresh
            )
            
            segments = []
            for start, end in silence_segments:
                segments.append({
                    'start': start / 1000.0,  # Convert to seconds
                    'end': end / 1000.0,
                    'duration': (end - start) / 1000.0
                })
            
            logger.info(f"Detected {len(segments)} silence segments")
            return segments
            
        except Exception as e:
            logger.error(f"Silence detection error: {str(e)}")
            raise
    
    def split_on_silence(self, audio_path: str, 
                        silence_thresh: int = -40,
                        min_silence_len: int = 500,
                        keep_silence: int = 100) -> List[AudioSegment]:
        """Split audio on silence"""
        try:
            audio = AudioSegment.from_file(audio_path)
            chunks = split_on_silence(
                audio,
                min_silence_len=min_silence_len,
                silence_thresh=silence_thresh,
                keep_silence=keep_silence
            )
            
            logger.info(f"Split audio into {len(chunks)} chunks")
            return chunks
            
        except Exception as e:
            logger.error(f"Audio splitting error: {str(e)}")
            raise
    
    def calculate_volume_levels(self, audio_path: str, 
                               window_size: float = 0.1) -> List[float]:
        """Calculate volume levels over time"""
        try:
            audio = AudioSegment.from_file(audio_path)
            samples = np.array(audio.get_array_of_samples())
            
            # Convert to floating point between -1 and 1
            if audio.sample_width == 2:
                samples = samples.astype(np.float32) / 32768.0
            elif audio.sample_width == 4:
                samples = samples.astype(np.float32) / 2147483648.0
            
            # Calculate RMS for each window
            window_samples = int(window_size * audio.frame_rate)
            volume_levels = []
            
            for i in range(0, len(samples), window_samples):
                window = samples[i:i + window_samples]
                if len(window) > 0:
                    rms = np.sqrt(np.mean(window**2))
                    volume_levels.append(rms)
            
            return volume_levels
            
        except Exception as e:
            logger.error(f"Volume calculation error: {str(e)}")
            raise
    
    def normalize_audio(self, input_path: str, output_path: str, 
                       target_dBFS: float = -20.0) -> str:
        """Normalize audio volume"""
        try:
            audio = AudioSegment.from_file(input_path)
            normalized_audio = audio.apply_gain(target_dBFS - audio.dBFS)
            normalized_audio.export(output_path, format="wav")
            
            logger.info(f"Audio normalized: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Audio normalization error: {str(e)}")
            raise
    
    def convert_sample_rate(self, input_path: str, output_path: str, 
                          sample_rate: int = 16000) -> str:
        """Convert audio sample rate"""
        try:
            audio = AudioSegment.from_file(input_path)
            converted_audio = audio.set_frame_rate(sample_rate)
            converted_audio.export(output_path, format="wav")
            
            logger.info(f"Sample rate converted to {sample_rate}Hz: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Sample rate conversion error: {str(e)}")
            raise