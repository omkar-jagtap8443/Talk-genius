# utils/video_processor.py
import os
import cv2
import numpy as np
# import ffmpeg  # Commented out due to FFmpeg not being installed
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class VideoProcessor:
    def __init__(self):
        self.supported_formats = ['.webm', '.mp4', '.avi', '.mov']
    
    def convert_to_mp4(self, input_path: str, output_path: Optional[str] = None) -> str:
        """Convert video to MP4 format - simplified without FFmpeg"""
        try:
            if not output_path:
                output_path = input_path.replace('.webm', '.mp4').replace('.avi', '.mp4')
            
            logger.info(f"Video conversion skipped (FFmpeg not available): {input_path}")
            
            # For now, just return the original path
            if input_path.endswith('.mp4'):
                return input_path
            else:
                logger.warning("FFmpeg not available - video conversion skipped")
                return input_path
            
        except Exception as e:
            logger.error(f"Video conversion error: {str(e)}")
            return input_path
    
    def extract_frames(self, video_path: str, interval: float = 1.0) -> List[np.ndarray]:
        """Extract frames from video at specified intervals"""
        frames = []
        try:
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_interval = int(fps * interval)
            
            frame_count = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                if frame_count % frame_interval == 0:
                    frames.append(frame)
                
                frame_count += 1
            
            cap.release()
            logger.info(f"Extracted {len(frames)} frames from {video_path}")
            return frames
            
        except Exception as e:
            logger.error(f"Frame extraction error: {str(e)}")
            raise
    
    def get_video_metadata(self, video_path: str) -> Dict:
        """Get video metadata"""
        try:
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                raise Exception("Cannot open video file")
            
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps if fps > 0 else 0
            
            cap.release()
            
            metadata = {
                'width': width,
                'height': height,
                'fps': fps,
                'frame_count': frame_count,
                'duration': duration,
                'file_size': os.path.getsize(video_path)
            }
            
            return metadata
            
        except Exception as e:
            logger.error(f"Metadata extraction error: {str(e)}")
            raise
    
    def compress_video(self, input_path: str, output_path: str, 
                      quality: str = 'medium') -> str:
        """Compress video file - simplified without FFmpeg"""
        logger.warning("Video compression not available without FFmpeg")
        return input_path
    
    def _parse_quality_preset(self, preset: str) -> Dict:
        """Parse quality preset string to ffmpeg parameters"""
        params = {}
        parts = preset.split()
        
        for i, part in enumerate(parts):
            if part == 'libx264':
                params['vcodec'] = 'libx264'
            elif part == '-crf' and i + 1 < len(parts):
                params['crf'] = parts[i + 1]
        
        return params
    
    def create_thumbnail(self, video_path: str, output_path: str, 
                        time_seconds: float = 10) -> str:
        """Create thumbnail from video using OpenCV"""
        try:
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                raise Exception("Cannot open video file")
            
            # Seek to the specified time
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_number = int(time_seconds * fps)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            
            ret, frame = cap.read()
            if ret:
                cv2.imwrite(output_path, frame)
                logger.info(f"Thumbnail created: {output_path}")
            else:
                logger.warning("Could not extract frame for thumbnail")
            
            cap.release()
            return output_path
            
        except Exception as e:
            logger.error(f"Thumbnail creation error: {str(e)}")
            return ""