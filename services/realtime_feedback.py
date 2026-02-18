# services/realtime_feedback.py
import time
import logging
from typing import Dict, List, Optional
from collections import deque
import numpy as np

logger = logging.getLogger(__name__)

class RealtimeFeedback:
    def __init__(self):
        self.active_sessions = {}
        self.feedback_history = {}
        
        # Feedback thresholds
        self.posture_thresholds = {
            'good': 80,
            'okay': 60,
            'poor': 0
        }
        
        self.eye_contact_thresholds = {
            'good': 75,
            'moderate': 50,
            'poor': 0
        }
        
        self.filler_word_thresholds = {
            'low': 2,      # per minute
            'medium': 5,   # per minute
            'high': 10     # per minute
        }
        
        self.pace_thresholds = {
            'too_slow': 120,
            'ideal_min': 140,
            'ideal_max': 160,
            'too_fast': 180
        }
    
    def start_session(self, session_id: str):
        """Initialize a new practice session"""
        self.active_sessions[session_id] = {
            'start_time': time.time(),
            'posture_scores': deque(maxlen=300),  # Last 5 minutes at 1Hz
            'eye_contact_scores': deque(maxlen=300),
            'filler_words': deque(maxlen=600),    # Track filler word timestamps
            'speech_data': {
                'word_count': 0,
                'last_word_time': None,
                'current_pace': 0
            },
            'feedback_messages': deque(maxlen=10),
            'metrics_history': {
                'posture': [],
                'eye_contact': [],
                'pace': [],
                'filler_rate': []
            }
        }
        
        self.feedback_history[session_id] = []
        logger.info(f"Started real-time feedback session: {session_id}")
    
    def analyze_frame(self, session_id: str, posture_data: Dict, 
                     audio_chunk: Optional[str] = None) -> Dict:
        """Analyze current frame and provide real-time feedback"""
        if session_id not in self.active_sessions:
            return self._get_empty_feedback()
        
        session = self.active_sessions[session_id]
        current_time = time.time()
        
        try:
            # Process posture data
            posture_feedback = self._analyze_posture(session_id, posture_data)
            
            # Process speech data if audio chunk provided
            speech_feedback = {}
            if audio_chunk:
                speech_feedback = self._analyze_speech(session_id, audio_chunk)
            
            # Combine feedback
            combined_feedback = self._combine_feedback(
                posture_feedback, speech_feedback
            )
            
            # Generate actionable suggestions
            suggestions = self._generate_suggestions(combined_feedback)
            
            # Update session metrics
            self._update_session_metrics(session_id, combined_feedback, current_time)
            
            feedback = {
                'timestamp': current_time,
                'posture': posture_feedback,
                'speech': speech_feedback,
                'suggestions': suggestions,
                'overall_score': self._calculate_overall_score(combined_feedback),
                'alert_level': self._determine_alert_level(combined_feedback)
            }
            
            # Store feedback in history
            self.feedback_history[session_id].append(feedback)
            session['feedback_messages'].append(feedback)
            
            return feedback
            
        except Exception as e:
            logger.error(f"Real-time analysis error: {str(e)}")
            return self._get_empty_feedback()
    
    def _analyze_posture(self, session_id: str, posture_data: Dict) -> Dict:
        """Analyze posture data for real-time feedback"""
        session = self.active_sessions[session_id]
        
        if not posture_data:
            return {
                'score': 0, 
                'eye_contact_score': 0,
                'posture_status': 'unknown', 
                'eye_contact_status': 'unknown',
                'posture_trend': 'stable',
                'eye_contact_trend': 'stable',
                'messages': {'posture': 'Ready to analyze...', 'eye_contact': 'Ready to analyze...'}
            }
        
        # Handle both direct scores and nested structure
        if isinstance(posture_data, dict):
            posture_score = posture_data.get('posture_score', posture_data.get('posture', {}).get('score', 0))
            eye_contact_score = posture_data.get('eye_contact_score', posture_data.get('eye_contact', {}).get('score', 0))
        else:
            posture_score = 0
            eye_contact_score = 0
        
        # Update session data with numeric values
        if posture_score > 0:
            session['posture_scores'].append(float(posture_score))
        if eye_contact_score > 0:
            session['eye_contact_scores'].append(float(eye_contact_score))
        
        # Calculate trends
        posture_trend = self._calculate_trend(list(session['posture_scores'])) if session['posture_scores'] else 'stable'
        eye_contact_trend = self._calculate_trend(list(session['eye_contact_scores'])) if session['eye_contact_scores'] else 'stable'
        
        # Generate feedback messages
        posture_message = self._get_posture_feedback(posture_score, posture_trend) if posture_score > 0 else 'Analyzing posture...'
        eye_contact_message = self._get_eye_contact_feedback(eye_contact_score, eye_contact_trend) if eye_contact_score > 0 else 'Analyzing eye contact...'
        
        return {
            'score': max(0, min(100, int(posture_score))),
            'eye_contact_score': max(0, min(100, int(eye_contact_score))),
            'posture_status': self._categorize_posture(posture_score),
            'eye_contact_status': self._categorize_eye_contact(eye_contact_score),
            'posture_trend': posture_trend,
            'eye_contact_trend': eye_contact_trend,
            'messages': {
                'posture': posture_message,
                'eye_contact': eye_contact_message
            }
        }
    
    def _analyze_speech(self, session_id: str, audio_chunk: str) -> Dict:
        """Analyze speech data for real-time feedback"""
        session = self.active_sessions[session_id]
        
        # This is a simplified version - in production, you'd use:
        # 1. Web Speech API for real-time transcription
        # 2. Audio analysis for pace and volume
        # 3. Filler word detection
        
        # For now, we'll simulate some speech analysis
        current_time = time.time()
        
        # Update speech metrics
        session['speech_data']['word_count'] += 1  # Simulated word count
        session['speech_data']['last_word_time'] = current_time
        
        # Calculate current pace (words per minute)
        session_duration = current_time - session['start_time']
        current_wpm = (session['speech_data']['word_count'] / session_duration * 60 
                      if session_duration > 0 else 0)
        session['speech_data']['current_pace'] = current_wpm
        
        # Simulate filler word detection (in real app, this would come from speech recognition)
        if np.random.random() < 0.05:  # 5% chance of filler word
            session['filler_words'].append(current_time)
        
        # Calculate filler word rate (per minute)
        recent_fillers = [t for t in session['filler_words'] 
                         if current_time - t < 60]  # Last minute
        filler_rate = len(recent_fillers)
        
        return {
            'current_wpm': round(current_wpm),
            'filler_rate': filler_rate,
            'pace_status': self._categorize_pace(current_wpm),
            'filler_status': self._categorize_filler_rate(filler_rate),
            'messages': {
                'pace': self._get_pace_feedback(current_wpm),
                'filler_words': self._get_filler_feedback(filler_rate)
            }
        }
    
    def _combine_feedback(self, posture_feedback: Dict, speech_feedback: Dict) -> Dict:
        """Combine posture and speech feedback"""
        return {
            'posture': posture_feedback,
            'speech': speech_feedback,
            'timestamp': time.time()
        }
    
    def _generate_suggestions(self, feedback: Dict) -> List[str]:
        """Generate actionable suggestions based on current feedback"""
        suggestions = []
        
        posture_data = feedback.get('posture', {})
        speech_data = feedback.get('speech', {})
        
        posture_score = posture_data.get('score', 0)
        eye_contact_score = posture_data.get('eye_contact_score', 0)
        wpm = speech_data.get('current_wpm', 0)
        filler_rate = speech_data.get('filler_rate', 0)
        
        # Don't give suggestions if no data yet
        if posture_score == 0 and eye_contact_score == 0 and wpm == 0:
            return ["Start speaking to get real-time feedback..."]
        
        # Posture suggestions
        posture_status = posture_data.get('posture_status', 'unknown')
        if posture_status == 'poor' and posture_score > 0:
            suggestions.append("Sit up straight - align your shoulders with your hips")
        
        # Eye contact suggestions
        eye_status = posture_data.get('eye_contact_status', 'unknown')
        if eye_status == 'poor' and eye_contact_score > 0:
            suggestions.append("Look directly at the camera for better engagement")
        
        # Speech pace suggestions
        pace_status = speech_data.get('pace_status', 'ideal')
        if pace_status == 'too_slow' and wpm > 0:
            suggestions.append("Speak a bit faster to maintain audience interest")
        elif pace_status == 'too_fast' and wpm > 0:
            suggestions.append("Slow down slightly for better clarity")
        
        # Filler words suggestions
        filler_status = speech_data.get('filler_status', 'low')
        if filler_status == 'high' and filler_rate > 0:
            suggestions.append("Practice pausing instead of using filler words")
        elif filler_status == 'medium' and filler_rate > 0:
            suggestions.append("Watch for occasional filler words like 'um' or 'like'")
        
        # Positive reinforcement
        overall_score = feedback.get('overall_score', 0)
        if overall_score >= 80:
            if not suggestions:  # Only add if no negative suggestions
                suggestions.append("Great job! Your delivery is confident and clear")
        
        # Remove duplicates and limit to 3 suggestions
        suggestions = list(dict.fromkeys(suggestions))[:3]
        
        # If no suggestions yet, provide encouraging message
        if not suggestions:
            suggestions.append("Keep practicing and you'll improve!")
        
        return suggestions
    
    def _calculate_overall_score(self, feedback: Dict) -> int:
        """Calculate overall performance score (0-100)"""
        try:
            posture_data = feedback.get('posture', {})
            posture_score = float(posture_data.get('score', 0))
            eye_contact_score = float(posture_data.get('eye_contact_score', 0))
            
            speech_data = feedback.get('speech', {})
            wpm = float(speech_data.get('current_wpm', 0))
            filler_rate = float(speech_data.get('filler_rate', 0))
            
            # Normalize WPM score (ideal range: 140-160)
            if 140 <= wpm <= 160:
                pace_score = 100
            elif wpm == 0:
                pace_score = 50  # Unknown/not started
            else:
                pace_score = max(0, 100 - abs(wpm - 150) * 2)
            
            # Normalize filler score (starts at 100, decreases with filler words)
            filler_score = max(0, 100 - (filler_rate * 10)) if filler_rate > 0 else 100
            
            # Use available data
            # If posture_score is 0, don't penalize yet (still analyzing)
            if posture_score == 0 and eye_contact_score == 0:
                # Still analyzing initial frames
                return 50
            
            # Weighted average - adjust weights based on available data
            total_weight = 0
            weighted_score = 0
            
            if posture_score > 0:
                weighted_score += posture_score * 0.3
                total_weight += 0.3
            
            if eye_contact_score > 0:
                weighted_score += eye_contact_score * 0.3
                total_weight += 0.3
            
            weighted_score += pace_score * 0.25
            total_weight += 0.25
            
            weighted_score += filler_score * 0.15
            total_weight += 0.15
            
            # Normalize if we don't have all scores yet
            if total_weight > 0:
                overall_score = weighted_score / total_weight
            else:
                overall_score = 50
            
            return int(max(0, min(100, overall_score)))
        except Exception as e:
            logger.error(f"Error calculating overall score: {e}")
            return 50
    
    def _determine_alert_level(self, feedback: Dict) -> str:
        """Determine the alert level for real-time display"""
        score = self._calculate_overall_score(feedback)
        
        if score >= 80:
            return 'excellent'
        elif score >= 60:
            return 'good'
        elif score >= 40:
            return 'needs_improvement'
        else:
            return 'poor'
    
    def _categorize_posture(self, score: float) -> str:
        if score >= self.posture_thresholds['good']:
            return 'good'
        elif score >= self.posture_thresholds['okay']:
            return 'okay'
        else:
            return 'poor'
    
    def _categorize_eye_contact(self, score: float) -> str:
        if score >= self.eye_contact_thresholds['good']:
            return 'good'
        elif score >= self.eye_contact_thresholds['moderate']:
            return 'moderate'
        else:
            return 'poor'
    
    def _categorize_pace(self, wpm: float) -> str:
        if wpm < self.pace_thresholds['too_slow']:
            return 'too_slow'
        elif wpm < self.pace_thresholds['ideal_min']:
            return 'slightly_slow'
        elif wpm <= self.pace_thresholds['ideal_max']:
            return 'ideal'
        elif wpm <= self.pace_thresholds['too_fast']:
            return 'slightly_fast'
        else:
            return 'too_fast'
    
    def _categorize_filler_rate(self, rate: float) -> str:
        if rate <= self.filler_word_thresholds['low']:
            return 'low'
        elif rate <= self.filler_word_thresholds['medium']:
            return 'medium'
        else:
            return 'high'
    
    def _get_posture_feedback(self, score: float, trend: str) -> str:
        if score >= 80:
            return "Great posture! You're projecting confidence."
        elif score >= 60:
            if trend == 'improving':
                return "Posture is improving. Keep your shoulders back."
            else:
                return "Good posture. Try to sit up a bit straighter."
        else:
            return "Adjust your posture. Sit up straight and align your shoulders."
    
    def _get_eye_contact_feedback(self, score: float, trend: str) -> str:
        if score >= 75:
            return "Excellent eye contact with the audience."
        elif score >= 50:
            return "Good eye contact. Try to look directly at the camera more."
        else:
            return "Focus on looking at the camera to engage your audience."
    
    def _get_pace_feedback(self, wpm: float) -> str:
        if 140 <= wpm <= 160:
            return "Perfect speaking pace - clear and engaging."
        elif wpm < 120:
            return "Your pace is slow. Try to speak a bit faster."
        elif wpm > 180:
            return "You're speaking quickly. Slow down for better clarity."
        else:
            return "Good speaking pace. Maintain this rhythm."
    
    def _get_filler_feedback(self, rate: float) -> str:
        if rate <= 2:
            return "Excellent control of filler words."
        elif rate <= 5:
            return "Good speech clarity. Watch for occasional filler words."
        else:
            return "Try pausing instead of using filler words like 'um' or 'like'."
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend of recent values"""
        if len(values) < 2:
            return 'stable'
        
        recent = values[-10:] if len(values) >= 10 else values  # Use last 10 or all values
        
        if len(recent) < 2:
            return 'stable'
        
        try:
            # Simple linear trend calculation
            x = np.arange(len(recent))
            if len(recent) >= 2:
                coefficients = np.polyfit(x, recent, 1)
                slope = coefficients[0]
                
                if slope > 1:
                    return 'improving'
                elif slope < -1:
                    return 'declining'
                else:
                    return 'stable'
            else:
                return 'stable'
        except:
            return 'stable'
    
    def _update_session_metrics(self, session_id: str, feedback: Dict, timestamp: float):
        """Update session metrics history"""
        session = self.active_sessions[session_id]
        
        session['metrics_history']['posture'].append({
            'timestamp': timestamp,
            'value': feedback.get('posture', {}).get('score', 0)
        })
        
        session['metrics_history']['eye_contact'].append({
            'timestamp': timestamp,
            'value': feedback.get('posture', {}).get('eye_contact_score', 0)
        })
        
        session['metrics_history']['pace'].append({
            'timestamp': timestamp,
            'value': feedback.get('speech', {}).get('current_wpm', 0)
        })
        
        session['metrics_history']['filler_rate'].append({
            'timestamp': timestamp,
            'value': feedback.get('speech', {}).get('filler_rate', 0)
        })
    
    def get_session_summary(self, session_id: str) -> Dict:
        """Get summary of session performance"""
        if session_id not in self.active_sessions:
            return {}
        
        session = self.active_sessions[session_id]
        history = self.feedback_history.get(session_id, [])
        
        if not history:
            return {}
        
        # Calculate averages
        posture_scores = [f['posture']['score'] for f in history if f['posture']['score'] > 0]
        eye_contact_scores = [f['posture']['eye_contact_score'] for f in history if f['posture']['eye_contact_score'] > 0]
        overall_scores = [f['overall_score'] for f in history]
        
        return {
            'duration': time.time() - session['start_time'],
            'average_posture': np.mean(posture_scores) if posture_scores else 0,
            'average_eye_contact': np.mean(eye_contact_scores) if eye_contact_scores else 0,
            'average_overall_score': np.mean(overall_scores) if overall_scores else 0,
            'feedback_count': len(history),
            'last_feedback': history[-1] if history else {}
        }
    
    def end_session(self, session_id: str):
        """Clean up session data"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
        if session_id in self.feedback_history:
            del self.feedback_history[session_id]
    
    def _get_empty_feedback(self) -> Dict:
        """Return empty feedback structure"""
        return {
            'timestamp': time.time(),
            'posture': {'score': 0, 'messages': {}},
            'speech': {'messages': {}},
            'suggestions': [],
            'overall_score': 0,
            'alert_level': 'unknown'
        }