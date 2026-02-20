# app.py - Main Flask Application
from flask import Flask, render_template, request, jsonify, send_from_directory, session, redirect, url_for
from flask_cors import CORS
import os
import time
import json
import uuid
from datetime import datetime
import logging

# Import custom utilities
from utils.video_processor import VideoProcessor
from utils.audio_processor import AudioProcessor
from utils.posture_analyzer import PostureAnalyzer
from utils.speech_analyzer import SpeechAnalyzer
from utils.gemini_client import GeminiClient
from utils.deepgram_client import DeepgramClient
from utils.file_processor import FileProcessor
from services.realtime_feedback import RealtimeFeedback
from services.scoring_engine import ScoringEngine
from services.topic_extractor import TopicExtractor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'talkgenius-practice-mirror-secret-key-2024'
CORS(app)

# Configuration
app.config.update(
    UPLOAD_FOLDER='data/uploads',
    VIDEOS_FOLDER='data/videos',
    AUDIO_FOLDER='data/audio',
    TRANSCRIPTS_FOLDER='data/transcripts',
    POSTURE_FOLDER='data/posture',
    ANALYSIS_FOLDER='data/analysis',
    REPORTS_FOLDER='data/reports',
    LLM_FOLDER='data/llm',
    MAX_CONTENT_LENGTH=100 * 1024 * 1024  # 100MB max file size
)

# Create directories
for folder in [app.config[key] for key in [
    'UPLOAD_FOLDER', 'VIDEOS_FOLDER', 'AUDIO_FOLDER', 'TRANSCRIPTS_FOLDER',
    'POSTURE_FOLDER', 'ANALYSIS_FOLDER', 'REPORTS_FOLDER', 'LLM_FOLDER'
]]:
    os.makedirs(folder, exist_ok=True)

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
            
            # Save uploaded file
            file_ext = os.path.splitext(file.filename)[1].lower()
            filename = f"{session_id}{file_ext}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Extract content and topics
            if file_ext in ['.ppt', '.pptx']:
                content = file_processor.extract_ppt_content(filepath)
            elif file_ext == '.pdf':
                content = file_processor.extract_pdf_content(filepath)
            else:
                return jsonify({'success': False, 'error': 'Unsupported file format'})
            
            # Extract main topic and keywords
            topic_data = topic_extractor.extract_from_content(content)
            
            session['topic'] = topic_data['main_topic']
            session['topic_type'] = 'file'
            session['topic_keywords'] = topic_data['keywords']
            session['file_content'] = content
            
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
        
        # Get data from request
        video_blob = request.files.get('video')
        posture_data = request.form.get('posture_data')
        audio_data = request.files.get('audio')
        
        if not video_blob:
            return jsonify({'success': False, 'error': 'No video data'})
        
        # Save video file
        video_filename = f"{session_id}.webm"
        video_path = os.path.join(app.config['VIDEOS_FOLDER'], video_filename)
        video_blob.save(video_path)
        
        # Convert to MP4
        mp4_path = video_processor.convert_to_mp4(video_path)
        
        # Extract audio
        audio_path = audio_processor.extract_audio(mp4_path)
        
        # Process posture data
        posture_analysis = None
        if posture_data:
            try:
                posture_raw = json.loads(posture_data)
                logger.info(f"Raw posture data received: {len(posture_raw.get('posture', []))} posture points, {len(posture_raw.get('eye_contact', []))} eye contact points")
                posture_analysis = posture_analyzer.process_posture_data(posture_raw)
                logger.info(f"Processed posture analysis: {posture_analysis}")
                posture_filename = f"{session_id}.json"
                posture_filepath = os.path.join(app.config['POSTURE_FOLDER'], posture_filename)
                with open(posture_filepath, 'w') as f:
                    json.dump(posture_analysis, f, indent=2)
            except Exception as e:
                logger.error(f"Error processing posture data: {str(e)}")
                posture_analysis = posture_analyzer._get_empty_analysis()
        else:
            # Provide default posture analysis if no data available
            logger.warning("No posture data provided")
            posture_analysis = posture_analyzer._get_empty_analysis()
        
        # Transcribe audio
        transcript = deepgram_client.transcribe_audio(audio_path)
        transcript_filename = f"{session_id}.json"
        transcript_filepath = os.path.join(app.config['TRANSCRIPTS_FOLDER'], transcript_filename)
        with open(transcript_filepath, 'w') as f:
            json.dump(transcript, f, indent=2)
        
        # Analyze speech
        speech_analysis = speech_analyzer.analyze_transcript(transcript)
        analysis_filename = f"{session_id}.json"
        analysis_filepath = os.path.join(app.config['ANALYSIS_FOLDER'], analysis_filename)
        with open(analysis_filepath, 'w') as f:
            json.dump(speech_analysis, f, indent=2)
        
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
        
        # Save report
        report_filename = f"{session_id}.json"
        report_filepath = os.path.join(app.config['REPORTS_FOLDER'], report_filename)
        with open(report_filepath, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        # Generate AI feedback using Gemini
        ai_feedback = gemini_client.generate_feedback(report_data)
        llm_filename = f"{session_id}.json"
        llm_filepath = os.path.join(app.config['LLM_FOLDER'], llm_filename)
        with open(llm_filepath, 'w') as f:
            json.dump(ai_feedback, f, indent=2)
        
        # Update report with AI feedback
        report_data['ai_feedback'] = ai_feedback
        with open(report_filepath, 'w') as f:
            json.dump(report_data, f, indent=2)
        
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
        report_path = os.path.join(app.config['REPORTS_FOLDER'], f"{session_id}.json")
        
        if not os.path.exists(report_path):
            return jsonify({'success': False, 'error': 'Report not found'})
        
        with open(report_path, 'r') as f:
            report_data = json.load(f)
        
        return jsonify({
            'success': True,
            'report': report_data
        })
        
    except Exception as e:
        logger.error(f"Error getting report: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/video/<session_id>')
def serve_video(session_id):
    """Serve recorded video by session ID"""
    try:
        return send_from_directory(app.config['VIDEOS_FOLDER'], f"{session_id}.mp4")
    except FileNotFoundError:
        return jsonify({'error': 'Video not found'}), 404

@app.route('/video')
def serve_latest_video():
    """Serve latest recorded video (for playback page)"""
    try:
        videos = [f for f in os.listdir(app.config['VIDEOS_FOLDER']) if f.endswith('.mp4')]
        if not videos:
            return jsonify({'error': 'No videos found'}), 404
        
        # Get the most recent video file
        latest_video = max(videos, key=lambda x: os.path.getctime(
            os.path.join(app.config['VIDEOS_FOLDER'], x)
        ))
        
        return send_from_directory(app.config['VIDEOS_FOLDER'], latest_video)
        
    except Exception as e:
        logger.error(f"Error serving video: {str(e)}")
        return jsonify({'error': 'Video not found'}), 404

@app.route('/report')
def serve_latest_report():
    """Serve latest report (for playback page)"""
    try:
        reports = os.listdir(app.config['REPORTS_FOLDER'])
        if not reports:
            return jsonify({'error': 'No reports found', 'message': 'Please complete a practice session first'}), 404
        
        latest_report = max(reports, key=lambda x: os.path.getctime(
            os.path.join(app.config['REPORTS_FOLDER'], x)
        ))
        
        with open(os.path.join(app.config['REPORTS_FOLDER'], latest_report), 'r') as f:
            report_data = json.load(f)
        
        return jsonify(report_data)
        
    except Exception as e:
        logger.error(f"Error serving report: {str(e)}")
        return jsonify({'error': str(e), 'message': 'Failed to load report data'}), 500

@app.route('/transcript')
def serve_latest_transcript():
    """Serve latest transcript"""
    try:
        transcripts = os.listdir(app.config['TRANSCRIPTS_FOLDER'])
        if not transcripts:
            return jsonify({'error': 'No transcripts found', 'message': 'Please complete a practice session first'}), 404
        
        latest_transcript = max(transcripts, key=lambda x: os.path.getctime(
            os.path.join(app.config['TRANSCRIPTS_FOLDER'], x)
        ))
        
        with open(os.path.join(app.config['TRANSCRIPTS_FOLDER'], latest_transcript), 'r') as f:
            transcript_data = json.load(f)
        
        return jsonify(transcript_data)
        
    except Exception as e:
        logger.error(f"Error serving transcript: {str(e)}")
        return jsonify({'error': str(e), 'message': 'Failed to load transcript data'}), 500

@app.route('/analysis_data')
def serve_latest_analysis():
    """Serve latest analysis"""
    try:
        analyses = os.listdir(app.config['ANALYSIS_FOLDER'])
        if not analyses:
            return jsonify({'error': 'No analysis found', 'message': 'Please complete a practice session first'}), 404
        
        latest_analysis = max(analyses, key=lambda x: os.path.getctime(
            os.path.join(app.config['ANALYSIS_FOLDER'], x)
        ))
        
        with open(os.path.join(app.config['ANALYSIS_FOLDER'], latest_analysis), 'r') as f:
            analysis_data = json.load(f)
        
        return jsonify(analysis_data)
        
    except Exception as e:
        logger.error(f"Error serving analysis: {str(e)}")
        return jsonify({'error': str(e), 'message': 'Failed to load analysis data'}), 500

@app.route('/llm_feedback')
def serve_llm_feedback():
    """Serve LLM feedback"""
    try:
        feedback_files = os.listdir(app.config['LLM_FOLDER'])
        if not feedback_files:
            return jsonify({'error': 'No LLM feedback found', 'message': 'Please complete a practice session first'}), 404
        
        latest_feedback = max(feedback_files, key=lambda x: os.path.getctime(
            os.path.join(app.config['LLM_FOLDER'], x)
        ))
        
        with open(os.path.join(app.config['LLM_FOLDER'], latest_feedback), 'r') as f:
            feedback_data = json.load(f)
        
        return jsonify(feedback_data)
        
    except Exception as e:
        logger.error(f"Error serving LLM feedback: {str(e)}")
        return jsonify({'error': str(e), 'message': 'Failed to load AI feedback'}), 500

@app.route('/session_history')
def get_session_history():
    """Get user's practice session history"""
    try:
        reports = []
        for filename in os.listdir(app.config['REPORTS_FOLDER']):
            if filename.endswith('.json'):
                filepath = os.path.join(app.config['REPORTS_FOLDER'], filename)
                with open(filepath, 'r') as f:
                    report_data = json.load(f)
                    reports.append({
                        'session_id': report_data.get('session_id'),
                        'timestamp': report_data.get('timestamp'),
                        'topic': report_data.get('topic'),
                        'overall_score': report_data.get('overall_score', {}).get('total', 0),
                        'duration': report_data.get('speech_analysis', {}).get('duration_seconds', 0)
                    })
        
        # Sort by timestamp (newest first)
        reports.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return jsonify({
            'success': True,
            'sessions': reports
        })
        
    except Exception as e:
        logger.error(f"Error getting session history: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    logger.info("Starting TalkGenius Practice Mirror...")
    app.run(debug=True, host='0.0.0.0', port=5000)