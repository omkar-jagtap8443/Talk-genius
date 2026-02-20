# app.py - Main Flask Application
from flask import Flask, render_template, request, jsonify, send_from_directory, session, redirect, url_for
from flask_cors import CORS
import os
import time
import json
import uuid
import tempfile
from datetime import datetime
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import custom utilities
from utils.video_processor import VideoProcessor
from utils.audio_processor import AudioProcessor
from utils.posture_analyzer import PostureAnalyzer
from utils.speech_analyzer import SpeechAnalyzer
from utils.gemini_client import GeminiClient
from utils.deepgram_client import DeepgramClient
from utils.file_processor import FileProcessor
from utils.supabase_storage import supabase_manager
from services.realtime_feedback import RealtimeFeedback
from services.scoring_engine import ScoringEngine
from services.topic_extractor import TopicExtractor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'talkgenius-practice-mirror-secret-key-2024')
CORS(app)

# Configuration
STORAGE_FOLDERS = {
    'UPLOAD_FOLDER': 'uploads',
    'VIDEOS_FOLDER': 'videos',
    'AUDIO_FOLDER': 'audio',
    'TRANSCRIPTS_FOLDER': 'transcripts',
    'POSTURE_FOLDER': 'posture',
    'ANALYSIS_FOLDER': 'analysis',
    'REPORTS_FOLDER': 'reports',
    'LLM_FOLDER': 'llm'
}

app.config.update(STORAGE_FOLDERS)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024

# Initialize services
video_processor = VideoProcessor()
audio_processor = AudioProcessor()
posture_analyzer = PostureAnalyzer()
speech_analyzer = SpeechAnalyzer()
gemini_client = GeminiClient()
deepgram_client = DeepgramClient()
file_processor = FileProcessor()
realtime_feedback = RealtimeFeedback()
scoring_engine = ScoringEngine()
topic_extractor = TopicExtractor()

@app.route('/')
def index():
    """Main landing page with topic selection"""
    return render_template('index.html')

@app.route('/practise')
def practice():
    """Practice recording interface"""
    return render_template('practise.html')

@app.route('/analysis')
def analysis():
    """Analysis results page"""
    return render_template('playback.html')

@app.route('/upload_topic', methods=['POST'])
def upload_topic():
    """Handle topic selection or file upload"""
    try:
        session_id = str(uuid.uuid4())
        session['session_id'] = session_id
        
        if 'topic_text' in request.form:
            # Text topic input
            topic_text = request.form['topic_text']
            session['topic'] = topic_text
            session['topic_type'] = 'text'
            
            # Extract keywords from topic
            keywords = topic_extractor.extract_keywords(topic_text)
            session['topic_keywords'] = keywords
            
            # Save session to Supabase
            supabase_manager.create_session(
                session_id, topic_text, 'text', keywords
            )
            
            return jsonify({
                'success': True,
                'session_id': session_id,
                'topic': topic_text,
                'keywords': keywords
            })
            
        elif 'ppt_pdf' in request.files:
            # File upload (PPT/PDF)
            file = request.files['ppt_pdf']
            if file.filename == '':
                return jsonify({'success': False, 'error': 'No file selected'})
            
            file_ext = os.path.splitext(file.filename)[1].lower()
            filename = f"{session_id}{file_ext}"
            
            # Extract content and topics
            if file_ext in ['.ppt', '.pptx']:
                content = file_processor.extract_ppt_content(file)
            elif file_ext == '.pdf':
                content = file_processor.extract_pdf_content(file)
            else:
                return jsonify({'success': False, 'error': 'Unsupported file format'})
            
            # Extract main topic and keywords
            topic_data = topic_extractor.extract_from_content(content)
            
            session['topic'] = topic_data['main_topic']
            session['topic_type'] = 'file'
            session['topic_keywords'] = topic_data['keywords']
            session['file_content'] = content
            
            # Save session and file to Supabase
            supabase_manager.create_session(
                session_id,
                topic_data['main_topic'],
                'file',
                topic_data['keywords'],
                content
            )
            supabase_manager.save_file(
                app.config['UPLOAD_FOLDER'],
                filename,
                file.read()
            )
            
            return jsonify({
                'success': True,
                'session_id': session_id,
                'topic': topic_data['main_topic'],
                'keywords': topic_data['keywords'],
                'content_preview': content[:500] + '...' if len(content) > 500 else content
            })
            
    except Exception as e:
        logger.error(f"Error in upload_topic: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/start_recording', methods=['POST'])
def start_recording():
    """Initialize recording session"""
    try:
        session_id = session.get('session_id')
        if not session_id:
            return jsonify({'success': False, 'error': 'No active session'})
        
        # Initialize real-time feedback
        realtime_feedback.start_session(session_id)
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'topic': session.get('topic', ''),
            'timestamp': int(time.time())
        })
        
    except Exception as e:
        logger.error(f"Error starting recording: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/realtime_feedback', methods=['POST'])
def get_realtime_feedback():
    """Get real-time feedback during recording"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        posture_data = data.get('posture_data', {})
        audio_chunk = data.get('audio_chunk')  # Base64 encoded audio chunk
        recording_time = data.get('recording_time', 0)
        
        if not session_id:
            return jsonify({'success': False, 'error': 'No session ID'})
        
        # Ensure session exists in realtime feedback
        if session_id not in realtime_feedback.active_sessions:
            realtime_feedback.start_session(session_id)
        
        # Process real-time feedback with structured posture data
        feedback = realtime_feedback.analyze_frame(
            session_id, 
            posture_data, 
            audio_chunk
        )
        
        return jsonify({
            'success': True,
            'feedback': feedback
        })
        
    except Exception as e:
        logger.error(f"Error in realtime_feedback: {str(e)}")
        return jsonify({
            'success': False, 
            'error': str(e),
            'feedback': {
                'posture': {'score': 0, 'messages': {}},
                'speech': {'messages': {}},
                'suggestions': [],
                'overall_score': 0,
                'alert_level': 'unknown'
            }
        })

@app.route('/save_recording', methods=['POST'])
def save_recording():
    """Save completed recording and process analysis"""
    try:
        session_id = session.get('session_id')
        if not session_id:
            return jsonify({'success': False, 'error': 'No active session'})
        
        video_blob = request.files.get('video')
        posture_data = request.form.get('posture_data')
        
        if not video_blob:
            return jsonify({'success': False, 'error': 'No video data'})
        
        # Read video bytes
        video_bytes = video_blob.read()
        
        # Save WebM to Supabase storage
        video_filename = f"{session_id}.webm"
        supabase_manager.save_file(
            app.config['VIDEOS_FOLDER'],
            video_filename,
            video_bytes
        )
        
        # Convert to MP4 (requires temp file)
        with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as tmp_file:
            tmp_file.write(video_bytes)
            tmp_webm_path = tmp_file.name
        
        mp4_path = video_processor.convert_to_mp4(tmp_webm_path)
        mp4_filename = f"{session_id}.mp4"
        
        # Read MP4 file and upload
        with open(mp4_path, 'rb') as f:
            mp4_bytes = f.read()
        
        supabase_manager.save_file(
            app.config['VIDEOS_FOLDER'],
            mp4_filename,
            mp4_bytes
        )
        
        # Extract audio
        audio_path = audio_processor.extract_audio(mp4_path)
        
        # Process posture data
        posture_analysis = None
        if posture_data:
            try:
                posture_raw = json.loads(posture_data)
                logger.info(f"Raw posture data: {len(posture_raw.get('posture', []))} points")
                posture_analysis = posture_analyzer.process_posture_data(posture_raw)
                
                # Save to Supabase database
                supabase_manager.save_posture_analysis(session_id, posture_analysis)
            except Exception as e:
                logger.error(f"Error processing posture data: {str(e)}")
                posture_analysis = posture_analyzer._get_empty_analysis()
        else:
            logger.warning("No posture data provided")
            posture_analysis = posture_analyzer._get_empty_analysis()
        
        # Transcribe audio
        transcript = deepgram_client.transcribe_audio(audio_path)
        supabase_manager.save_transcript(session_id, transcript)
        
        # Analyze speech
        speech_analysis = speech_analyzer.analyze_transcript(transcript)
        supabase_manager.save_speech_analysis(session_id, speech_analysis)
        
        # Generate comprehensive report
        report_data = {
            'session_id': session_id,
            'timestamp': int(time.time()),
            'topic': session.get('topic'),
            'topic_type': session.get('topic_type'),
            'topic_keywords': session.get('topic_keywords', []),
            'posture_analysis': posture_analysis,
            'speech_analysis': speech_analysis,
            'transcript': transcript
        }
        
        # Calculate overall score
        overall_score = scoring_engine.calculate_overall_score(
            posture_analysis, 
            speech_analysis, 
            session.get('topic_keywords', [])
        )
        report_data['overall_score'] = overall_score
        
        # Generate AI feedback
        ai_feedback = gemini_client.generate_feedback(report_data)
        logger.info(f"Generated AI feedback - type: {type(ai_feedback)}")
        
        # Log before saving
        logger.info(f"Saving to database - report_data keys: {list(report_data.keys())}")
        logger.info(f"Saving to database - overall_score: {overall_score}")
        
        # Save report to Supabase database
        save_success = supabase_manager.save_report(
            session_id,
            report_data,
            overall_score,
            ai_feedback
        )
        logger.info(f"Report save success: {save_success}")
        
        # Also save files to storage for direct access
        supabase_manager.save_file(
            app.config['REPORTS_FOLDER'],
            f"{session_id}.json",
            report_data
        )
        supabase_manager.save_file(
            app.config['LLM_FOLDER'],
            f"{session_id}.json",
            ai_feedback
        )
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'overall_score': overall_score,
            'message': 'Recording processed successfully'
        })
        
    except Exception as e:
        logger.error(f"Error saving recording: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/get_report/<session_id>')
def get_report(session_id):
    """Get analysis report for a session"""
    try:
        report = supabase_manager.get_report(session_id)
        
        if not report:
            return jsonify({'success': False, 'error': 'Report not found'})
        
        return jsonify({
            'success': True,
            'report': report
        })
        
    except Exception as e:
        logger.error(f"Error getting report: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/video/<session_id>')
def serve_video(session_id):
    """Serve recorded video by session ID"""
    try:
        file_url = supabase_manager.get_file_url(
            app.config['VIDEOS_FOLDER'],
            f"{session_id}.mp4"
        )
        if file_url:
            return jsonify({'success': True, 'url': file_url})
        return jsonify({'error': 'Video not found'}), 404
    except Exception as e:
        logger.error(f"Error serving video: {str(e)}")
        return jsonify({'error': 'Video not found'}), 404

@app.route('/video')
def serve_latest_video():
    """Serve latest recorded video"""
    try:
        report = supabase_manager.get_latest_report()
        
        if not report:
            return jsonify({'error': 'No videos found'}), 404
        
        session_id = report['session_id']
        file_url = supabase_manager.get_file_url(
            app.config['VIDEOS_FOLDER'],
            f"{session_id}.mp4"
        )
        
        if file_url:
            return jsonify({'success': True, 'url': file_url})
        return jsonify({'error': 'Video not found'}), 404
        
    except Exception as e:
        logger.error(f"Error serving video: {str(e)}")
        return jsonify({'error': 'Video not found'}), 404

@app.route('/report')
def serve_latest_report():
    """Serve latest report"""
    try:
        report = supabase_manager.get_latest_report()
        logger.info(f"Latest report retrieved: {report is not None}")
        
        if not report:
            logger.warning("No report found in database")
            return jsonify({
                'error': 'No reports found',
                'message': 'Please complete a practice session first'
            }), 404
        
        # Extract report data from the database record
        report_data = report.get('report_data', report)
        logger.info(f"Report data keys: {report_data.keys() if isinstance(report_data, dict) else 'Not a dict'}")
        
        return jsonify(report_data)
        
    except Exception as e:
        logger.error(f"Error serving report: {str(e)}", exc_info=True)
        return jsonify({
            'error': str(e),
            'message': 'Failed to load report data'
        }), 500

@app.route('/transcript')
def serve_latest_transcript():
    """Serve latest transcript"""
    try:
        report = supabase_manager.get_latest_report()
        logger.info(f"Retrieving transcript from report: {report is not None}")
        
        if not report:
            logger.warning("No report found for transcript")
            return jsonify({
                'error': 'No transcripts found',
                'message': 'Please complete a practice session first'
            }), 404
        
        # First try to get from report_data
        report_data = report.get('report_data')
        if report_data and isinstance(report_data, dict):
            transcript = report_data.get('transcript')
            if transcript:
                logger.info("Transcript found in report_data")
                return jsonify(transcript)
        
        # Fall back to database query
        session_id = report.get('session_id')
        if session_id:
            transcript = supabase_manager.get_transcript(session_id)
            if transcript:
                logger.info("Transcript found in database")
                return jsonify(transcript)
        
        logger.warning(f"No transcript found for session {session_id}")
        return jsonify({'error': 'Transcript not found'}), 404
        
    except Exception as e:
        logger.error(f"Error serving transcript: {str(e)}", exc_info=True)
        return jsonify({
            'error': str(e),
            'message': 'Failed to load transcript data'
        }), 500

@app.route('/analysis_data')
def serve_latest_analysis():
    """Serve latest analysis"""
    try:
        report = supabase_manager.get_latest_report()
        logger.info(f"Retrieving analysis from report: {report is not None}")
        
        if not report:
            logger.warning("No report found for analysis")
            return jsonify({
                'error': 'No analysis found',
                'message': 'Please complete a practice session first'
            }), 404
        
        # First try to get from report_data
        report_data = report.get('report_data')
        if report_data and isinstance(report_data, dict):
            analysis = report_data.get('speech_analysis')
            if analysis:
                logger.info("Speech analysis found in report_data")
                return jsonify(analysis)
        
        # Fall back to database query
        session_id = report.get('session_id')
        if session_id:
            analysis = supabase_manager.get_speech_analysis(session_id)
            if analysis:
                logger.info("Speech analysis found in database")
                return jsonify(analysis)
        
        logger.warning(f"No analysis found for session {session_id}")
        return jsonify({'error': 'Analysis not found'}), 404
        
    except Exception as e:
        logger.error(f"Error serving analysis: {str(e)}", exc_info=True)
        return jsonify({
            'error': str(e),
            'message': 'Failed to load analysis data'
        }), 500

@app.route('/llm_feedback')
def serve_llm_feedback():
    """Serve LLM feedback"""
    try:
        report = supabase_manager.get_latest_report()
        
        if not report:
            return jsonify({
                'error': 'No LLM feedback found',
                'message': 'Please complete a practice session first'
            }), 404
        
        ai_feedback = report.get('ai_feedback')
        
        if ai_feedback:
            return jsonify(ai_feedback)
        return jsonify({'error': 'AI feedback not found'}), 404
        
    except Exception as e:
        logger.error(f"Error serving LLM feedback: {str(e)}")
        return jsonify({
            'error': str(e),
            'message': 'Failed to load AI feedback'
        }), 500

@app.route('/session_history')
def get_session_history():
    """Get user's practice session history"""
    try:
        sessions = supabase_manager.get_session_history(limit=50)
        
        return jsonify({
            'success': True,
            'sessions': sessions
        })
        
    except Exception as e:
        logger.error(f"Error getting session history: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/debug/latest_report')
def debug_latest_report():
    """Debug endpoint to see what's stored"""
    try:
        report = supabase_manager.get_latest_report()
        logger.info(f"DEBUG: Latest report: {report}")
        
        if not report:
            return jsonify({'debug': 'No report found'})
        
        return jsonify({
            'keys': list(report.keys()) if isinstance(report, dict) else 'Not a dict',
            'report': report
        })
    except Exception as e:
        logger.error(f"Debug error: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)})

@app.route('/debug/all_reports')
def debug_all_reports():
    """Debug endpoint to see all reports"""
    try:
        from supabase import create_client
        supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
        response = supabase.table('reports').select('*').order('created_at', desc=True).limit(5).execute()
        
        return jsonify({
            'count': len(response.data) if response.data else 0,
            'reports': response.data
        })
    except Exception as e:
        logger.error(f"Debug error: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    logger.info("Starting TalkGenius Practice Mirror with Supabase...")
    app.run(debug=True, host='0.0.0.0', port=5000)