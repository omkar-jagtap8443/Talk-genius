# utils/deepgram_client.py
import requests
import json
import logging
import base64
from typing import Dict, Optional
from config import Config

logger = logging.getLogger(__name__)

class DeepgramClient:
    def __init__(self):
        self.api_key = Config.DEEPGRAM_API_KEY
        self.base_url = "https://api.deepgram.com/v1/listen"
        self.headers = {
            'Authorization': f'Token {self.api_key}',
            'Content-Type': 'audio/wav'
        }
    
    def transcribe_audio(self, audio_path: str) -> Dict:
        """Transcribe audio file using Deepgram API"""
        if not self.api_key or self.api_key == 'your-deepgram-api-key':
            logger.warning("Deepgram API key not configured")
            return self._get_empty_transcript()
        
        try:
            logger.info(f"Transcribing audio file: {audio_path}")
            
            with open(audio_path, 'rb') as audio_file:
                audio_data = audio_file.read()
            
            params = {
                'punctuate': 'true',
                'diarize': 'true',
                'model': 'general',
                'tier': 'nova',
                'utterances': 'true',
                'paragraphs': 'true',
                'smart_format': 'true'
            }
            
            response = requests.post(
                self.base_url,
                headers=self.headers,
                params=params,
                data=audio_data,
                timeout=30
            )
            
            if response.status_code == 200:
                transcript_data = response.json()
                logger.info("Deepgram transcription completed successfully")
                return transcript_data
            else:
                logger.error(f"Deepgram API error: {response.status_code} - {response.text}")
                return self._get_empty_transcript()
                
        except Exception as e:
            logger.error(f"Deepgram transcription failed: {str(e)}")
            return self._get_empty_transcript()
    
    def transcribe_audio_chunk(self, audio_chunk: str) -> Dict:
        """Transcribe a base64 encoded audio chunk for real-time processing"""
        if not self.api_key or self.api_key == 'your-deepgram-api-key':
            return self._get_empty_transcript()
        
        try:
            # Decode base64 audio chunk
            audio_data = base64.b64decode(audio_chunk)
            
            params = {
                'punctuate': 'true',
                'model': 'general',
                'tier': 'nova',
                'utterances': 'true',
                'smart_format': 'true'
            }
            
            response = requests.post(
                self.base_url,
                headers=self.headers,
                params=params,
                data=audio_data,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Deepgram chunk transcription error: {response.status_code}")
                return self._get_empty_transcript()
                
        except Exception as e:
            logger.error(f"Chunk transcription failed: {str(e)}")
            return self._get_empty_transcript()
    
    def extract_transcript_text(self, transcript_data: Dict) -> str:
        """Extract plain text transcript from Deepgram response"""
        try:
            if not transcript_data or 'results' not in transcript_data:
                return ""
            
            channels = transcript_data['results'].get('channels', [])
            if not channels:
                return ""
            
            alternatives = channels[0].get('alternatives', [])
            if not alternatives:
                return ""
            
            return alternatives[0].get('transcript', '').strip()
            
        except Exception as e:
            logger.error(f"Transcript extraction error: {str(e)}")
            return ""
    
    def extract_words_with_timings(self, transcript_data: Dict) -> list:
        """Extract words with their start and end times"""
        try:
            if not transcript_data or 'results' not in transcript_data:
                return []
            
            channels = transcript_data['results'].get('channels', [])
            if not channels:
                return []
            
            alternatives = channels[0].get('alternatives', [])
            if not alternatives:
                return []
            
            return alternatives[0].get('words', [])
            
        except Exception as e:
            logger.error(f"Word extraction error: {str(e)}")
            return []
    
    def get_transcript_metadata(self, transcript_data: Dict) -> Dict:
        """Extract metadata from transcript response"""
        try:
            if not transcript_data or 'results' not in transcript_data:
                return {}
            
            metadata = transcript_data.get('metadata', {})
            channels = transcript_data['results'].get('channels', [])
            
            if not channels:
                return {}
            
            alternatives = channels[0].get('alternatives', [])
            if not alternatives:
                return {}
            
            # Calculate duration from word timings
            words = alternatives[0].get('words', [])
            duration = 0
            if words:
                duration = words[-1]['end'] - words[0]['start']
            
            return {
                'duration': duration,
                'word_count': len(words),
                'request_id': metadata.get('request_id', ''),
                'model_info': metadata.get('model_info', {}),
                'confidence': alternatives[0].get('confidence', 0)
            }
            
        except Exception as e:
            logger.error(f"Metadata extraction error: {str(e)}")
            return {}
    
    def is_available(self) -> bool:
        """Check if Deepgram client is available"""
        return bool(self.api_key and self.api_key != 'your-deepgram-api-key')
    
    def _get_empty_transcript(self) -> Dict:
        """Return empty transcript structure"""
        return {
            'results': {
                'channels': [
                    {
                        'alternatives': [
                            {
                                'transcript': '',
                                'confidence': 0,
                                'words': []
                            }
                        ]
                    }
                ]
            },
            'metadata': {
                'request_id': '',
                'model_info': {}
            }
        }