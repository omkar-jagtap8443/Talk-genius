import json
import logging
from supabase import create_client, Client
from typing import Optional, Dict, Any
import os

logger = logging.getLogger(__name__)

class SupabaseManager:
    """Manages all Supabase database and storage operations"""
    
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY')
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        self.bucket_name = 'practice-data'
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Ensure storage bucket exists"""
        try:
            self.supabase.storage.list_buckets()
            logger.info("Supabase connection established")
        except Exception as e:
            logger.error(f"Error connecting to Supabase: {str(e)}")
    
    # ==================== SESSION MANAGEMENT ====================
    
    def create_session(self, session_id: str, topic: str, topic_type: str, 
                      topic_keywords: list, file_content: Optional[str] = None) -> bool:
        """Create a new session record"""
        try:
            data = {
                'session_id': session_id,
                'topic': topic,
                'topic_type': topic_type,
                'topic_keywords': topic_keywords,
                'file_content': file_content
            }
            self.supabase.table('sessions').insert(data).execute()
            logger.info(f"Session created: {session_id}")
            return True
        except Exception as e:
            logger.error(f"Error creating session: {str(e)}")
            return False
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session details"""
        try:
            response = self.supabase.table('sessions').select('*').eq(
                'session_id', session_id
            ).execute()
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error getting session: {str(e)}")
            return None
    
    # ==================== POSTURE ANALYSIS ====================
    
    def save_posture_analysis(self, session_id: str, analysis_data: Dict) -> bool:
        """Save posture analysis to database"""
        try:
            data = {
                'session_id': session_id,
                'analysis_data': analysis_data
            }
            self.supabase.table('posture_analysis').upsert(data).execute()
            logger.info(f"Posture analysis saved: {session_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving posture analysis: {str(e)}")
            return False
    
    def get_posture_analysis(self, session_id: str) -> Optional[Dict]:
        """Get posture analysis"""
        try:
            response = self.supabase.table('posture_analysis').select('*').eq(
                'session_id', session_id
            ).execute()
            if response.data:
                return response.data[0]['analysis_data']
            return None
        except Exception as e:
            logger.error(f"Error getting posture analysis: {str(e)}")
            return None
    
    # ==================== SPEECH ANALYSIS ====================
    
    def save_speech_analysis(self, session_id: str, analysis_data: Dict) -> bool:
        """Save speech analysis to database"""
        try:
            data = {
                'session_id': session_id,
                'analysis_data': analysis_data
            }
            self.supabase.table('speech_analysis').upsert(data).execute()
            logger.info(f"Speech analysis saved: {session_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving speech analysis: {str(e)}")
            return False
    
    def get_speech_analysis(self, session_id: str) -> Optional[Dict]:
        """Get speech analysis"""
        try:
            response = self.supabase.table('speech_analysis').select('*').eq(
                'session_id', session_id
            ).execute()
            if response.data:
                return response.data[0]['analysis_data']
            return None
        except Exception as e:
            logger.error(f"Error getting speech analysis: {str(e)}")
            return None
    
    # ==================== TRANSCRIPTS ====================
    
    def save_transcript(self, session_id: str, transcript_data: Dict) -> bool:
        """Save transcript to database"""
        try:
            data = {
                'session_id': session_id,
                'transcript_data': transcript_data
            }
            self.supabase.table('transcripts').upsert(data).execute()
            logger.info(f"Transcript saved: {session_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving transcript: {str(e)}")
            return False
    
    def get_transcript(self, session_id: str) -> Optional[Dict]:
        """Get transcript"""
        try:
            response = self.supabase.table('transcripts').select('*').eq(
                'session_id', session_id
            ).execute()
            if response.data:
                return response.data[0]['transcript_data']
            return None
        except Exception as e:
            logger.error(f"Error getting transcript: {str(e)}")
            return None
    
    # ==================== REPORTS ====================
    
    def save_report(self, session_id: str, report_data: Dict, 
                   overall_score: Dict, ai_feedback: Dict) -> bool:
        """Save complete report to database"""
        try:
            data = {
                'session_id': session_id,
                'report_data': report_data,
                'overall_score': overall_score,
                'ai_feedback': ai_feedback
            }
            logger.info(f"Saving report - report_data keys: {list(report_data.keys())}")
            logger.info(f"Saving report - overall_score type: {type(overall_score)}")
            
            self.supabase.table('reports').upsert(data).execute()
            logger.info(f"Report saved: {session_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving report: {str(e)}", exc_info=True)
            return False
    
    def get_report(self, session_id: str) -> Optional[Dict]:
        """Get full report"""
        try:
            response = self.supabase.table('reports').select('*').eq(
                'session_id', session_id
            ).execute()
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error getting report: {str(e)}")
            return None
    
    def get_latest_report(self) -> Optional[Dict]:
        """Get most recent report"""
        try:
            response = self.supabase.table('reports').select('*').order(
                'created_at', desc=True
            ).limit(1).execute()
            if response.data:
                report = response.data[0]
                logger.info(f"Latest report retrieved - has keys: {list(report.keys())}")
                return report
            logger.warning("No reports found in database")
            return None
        except Exception as e:
            logger.error(f"Error getting latest report: {str(e)}", exc_info=True)
            return None
    
    def get_session_history(self, limit: int = 50) -> list:
        """Get session history"""
        try:
            response = self.supabase.table('session_history').select('*').order(
                'timestamp', desc=True
            ).limit(limit).execute()
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Error getting session history: {str(e)}")
            return []
    
    # ==================== FILE STORAGE ====================
    
    def save_file(self, folder: str, filename: str, file_content) -> bool:
        """Save file to Supabase storage"""
        try:
            path = f"{folder}/{filename}"
            
            if isinstance(file_content, dict):
                file_bytes = json.dumps(file_content).encode('utf-8')
            elif isinstance(file_content, str):
                file_bytes = file_content.encode('utf-8')
            elif hasattr(file_content, 'read'):
                # Handle file objects (FileStorage, etc.)
                file_bytes = file_content.read()
                if isinstance(file_bytes, str):
                    file_bytes = file_bytes.encode('utf-8')
            else:
                file_bytes = file_content
            
            self.supabase.storage.from_(self.bucket_name).upload(path, file_bytes)
            logger.info(f"File uploaded to Supabase: {path}")
            return True
        except Exception as e:
            logger.error(f"Error uploading file: {str(e)}")
            return False
    
    def get_file(self, folder: str, filename: str) -> Optional[bytes]:
        """Get file from Supabase storage"""
        try:
            path = f"{folder}/{filename}"
            file_data = self.supabase.storage.from_(self.bucket_name).download(path)
            logger.info(f"File downloaded from Supabase: {path}")
            return file_data
        except Exception as e:
            logger.error(f"Error downloading file: {str(e)}")
            return None
    
    def get_file_url(self, folder: str, filename: str) -> str:
        """Get public URL for file"""
        try:
            path = f"{folder}/{filename}"
            url = self.supabase.storage.from_(self.bucket_name).get_public_url(path)
            return url
        except Exception as e:
            logger.error(f"Error getting file URL: {str(e)}")
            return ""
    
    def list_files(self, folder: str) -> list:
        """List files in a folder"""
        try:
            files = self.supabase.storage.from_(self.bucket_name).list(folder)
            return [f['name'] for f in files] if files else []
        except Exception as e:
            logger.error(f"Error listing files: {str(e)}")
            return []
    
    def delete_file(self, folder: str, filename: str) -> bool:
        """Delete file from storage"""
        try:
            path = f"{folder}/{filename}"
            self.supabase.storage.from_(self.bucket_name).remove([path])
            logger.info(f"File deleted from Supabase: {path}")
            return True
        except Exception as e:
            logger.error(f"Error deleting file: {str(e)}")
            return False

# Create singleton instance
supabase_manager = SupabaseManager()
