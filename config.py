# config.py - Application Configuration
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'talkgenius-practice-mirror-secret-key-2024')
    
    # API Keys
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'your-gemini-api-key')
    DEEPGRAM_API_KEY = os.getenv('DEEPGRAM_API_KEY', 'your-deepgram-api-key')
    
    # Hugging Face Configuration
    HUGGINGFACE_API_KEY = os.getenv('HUGGINGFACE_API_KEY', 'your-huggingface-key')
    
    # Application Settings
    MAX_RECORDING_DURATION = 600  # 10 minutes maximum
    REAL_TIME_FEEDBACK_INTERVAL = 2  # seconds
    ALLOWED_EXTENSIONS = {'pdf', 'ppt', 'pptx', 'txt'}
    
    # Analysis Thresholds
    POSTURE_GOOD_THRESHOLD = 80
    POSTURE_OKAY_THRESHOLD = 60
    EYE_CONTACT_GOOD_THRESHOLD = 75
    FILLER_WORDS_WARNING = 5
    WPM_IDEAL_RANGE = (140, 160)
    
    # File Paths
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    
    @staticmethod
    def init_app(app):
        # Ensure data directories exist
        folders = [
            'uploads', 'videos', 'audio', 'transcripts', 
            'posture', 'analysis', 'reports', 'llm'
        ]
        for folder in folders:
            os.makedirs(os.path.join(Config.DATA_DIR, folder), exist_ok=True)