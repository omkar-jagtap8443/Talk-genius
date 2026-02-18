# services/scoring_engine.py
import logging
from typing import Dict, List, Tuple
import numpy as np

logger = logging.getLogger(__name__)

class ScoringEngine:
    def __init__(self):
        # Weight configurations for different aspects
        self.weights = {
            'posture': {
                'score': 0.15,
                'consistency': 0.05,
                'trend': 0.05
            },
            'eye_contact': {
                'score': 0.10,
                'consistency': 0.05
            },
            'speech': {
                'wpm': 0.10,
                'filler_words': 0.10,
                'pauses': 0.05,
                'repetition': 0.05,
                'grammar': 0.05
            },
            'content': {
                'relevance': 0.15,
                'structure': 0.05,
                'vocabulary': 0.05
            },
            'delivery': {
                'pace_consistency': 0.05,
                'volume_stability': 0.05
            }
        }
        
        # Ideal ranges and thresholds
        self.ideal_ranges = {
            'wpm': (140, 160),
            'filler_words_per_minute': (0, 3),
            'pause_ratio': (0.1, 0.3),  # Percentage of speaking time spent in pauses
            'posture_score': (80, 100),
            'eye_contact_score': (75, 100)
        }
    
    def calculate_overall_score(self, posture_analysis: Dict, 
                              speech_analysis: Dict,
                              topic_keywords: List[str] = None) -> Dict:
        """Calculate comprehensive overall score"""
        try:
            # Calculate individual component scores
            posture_score = self._calculate_posture_score(posture_analysis)
            eye_contact_score = self._calculate_eye_contact_score(posture_analysis)
            speech_scores = self._calculate_speech_scores(speech_analysis)
            content_score = self._calculate_content_score(speech_analysis, topic_keywords)
            delivery_score = self._calculate_delivery_score(speech_analysis)
            
            # Calculate weighted total
            total_score = (
                posture_score['total'] * self.weights['posture']['score'] +
                eye_contact_score['total'] * self.weights['eye_contact']['score'] +
                speech_scores['total'] * sum(self.weights['speech'].values()) +
                content_score['total'] * sum(self.weights['content'].values()) +
                delivery_score['total'] * sum(self.weights['delivery'].values())
            )
            
            # Calculate category scores
            category_scores = {
                'posture': posture_score,
                'eye_contact': eye_contact_score,
                'speech': speech_scores,
                'content': content_score,
                'delivery': delivery_score
            }
            
            # Determine performance level
            performance_level = self._get_performance_level(total_score)
            
            # Generate improvement recommendations
            recommendations = self._generate_recommendations(category_scores)
            
            return {
                'total': round(total_score, 1),
                'performance_level': performance_level,
                'category_scores': category_scores,
                'recommendations': recommendations,
                'breakdown': {
                    'posture': round(posture_score['total'], 1),
                    'eye_contact': round(eye_contact_score['total'], 1),
                    'speech': round(speech_scores['total'], 1),
                    'content': round(content_score['total'], 1),
                    'delivery': round(delivery_score['total'], 1)
                }
            }
            
        except Exception as e:
            logger.error(f"Score calculation error: {str(e)}")
            return self._get_empty_score()
    
    def _calculate_posture_score(self, posture_analysis: Dict) -> Dict:
        """Calculate posture-related scores"""
        if not posture_analysis:
            return {'total': 0, 'components': {}}
        
        summary = posture_analysis.get('summary', {})
        
        # Base score from average posture
        base_score = summary.get('average_posture_score', 0)
        
        # Consistency score (how stable was the posture)
        breakdown = summary.get('posture_breakdown', {})
        good_percentage = breakdown.get('good_percentage', 0)
        consistency_score = min(100, good_percentage * 1.2)  # Scale to 100
        
        # Trend consideration (if we had real-time data)
        trend_score = 80  # Default, would be calculated from real-time data
        
        components = {
            'base_score': base_score,
            'consistency': consistency_score,
            'trend': trend_score
        }
        
        total = (
            base_score * 0.7 +
            consistency_score * 0.2 +
            trend_score * 0.1
        )
        
        return {
            'total': total,
            'components': components
        }
    
    def _calculate_eye_contact_score(self, posture_analysis: Dict) -> Dict:
        """Calculate eye contact scores"""
        if not posture_analysis:
            return {'total': 0, 'components': {}}
        
        summary = posture_analysis.get('summary', {})
        
        # Base score from average eye contact
        base_score = summary.get('average_eye_contact_score', 0)
        
        # Consistency score
        breakdown = summary.get('eye_contact_breakdown', {})
        good_percentage = breakdown.get('good_percentage', 0)
        consistency_score = min(100, good_percentage * 1.2)
        
        components = {
            'base_score': base_score,
            'consistency': consistency_score
        }
        
        total = (
            base_score * 0.8 +
            consistency_score * 0.2
        )
        
        return {
            'total': total,
            'components': components
        }
    
    def _calculate_speech_scores(self, speech_analysis: Dict) -> Dict:
        """Calculate speech-related scores"""
        if not speech_analysis:
            return {'total': 0, 'components': {}}
        
        # WPM score
        wpm = speech_analysis.get('words_per_minute', 0)
        wpm_score = self._calculate_wpm_score(wpm)
        
        # Filler words score
        filler_data = speech_analysis.get('filler_words', {})
        filler_count = filler_data.get('total_count', 0)
        duration = speech_analysis.get('duration_seconds', 1)
        filler_rate = (filler_count / duration * 60) if duration > 0 else 0
        filler_score = self._calculate_filler_score(filler_rate)
        
        # Pauses score
        pause_data = speech_analysis.get('pauses', {})
        pause_score = self._calculate_pause_score(pause_data, duration)
        
        # Repetition score
        repetition_data = speech_analysis.get('repetition', {})
        repetition_score = self._calculate_repetition_score(repetition_data)
        
        # Grammar score
        grammar_data = speech_analysis.get('grammar_errors', {})
        grammar_score = self._calculate_grammar_score(grammar_data, speech_analysis.get('word_count', 1))
        
        components = {
            'wpm': wpm_score,
            'filler_words': filler_score,
            'pauses': pause_score,
            'repetition': repetition_score,
            'grammar': grammar_score
        }
        
        total = sum(score * self.weights['speech'][key] 
                   for key, score in components.items()) / sum(self.weights['speech'].values())
        
        return {
            'total': total,
            'components': components
        }
    
    def _calculate_content_score(self, speech_analysis: Dict, topic_keywords: List[str]) -> Dict:
        """Calculate content quality scores"""
        if not speech_analysis:
            return {'total': 0, 'components': {}}
        
        transcript = speech_analysis.get('transcript', '').lower()
        word_count = speech_analysis.get('word_count', 0)
        
        # Relevance score (based on topic keywords)
        relevance_score = self._calculate_relevance_score(transcript, topic_keywords)
        
        # Structure score (based on sentence variety and length)
        structure_score = self._calculate_structure_score(transcript, word_count)
        
        # Vocabulary score (based on word variety)
        vocabulary_score = self._calculate_vocabulary_score(speech_analysis)
        
        components = {
            'relevance': relevance_score,
            'structure': structure_score,
            'vocabulary': vocabulary_score
        }
        
        total = (
            relevance_score * 0.6 +
            structure_score * 0.2 +
            vocabulary_score * 0.2
        )
        
        return {
            'total': total,
            'components': components
        }
    
    def _calculate_delivery_score(self, speech_analysis: Dict) -> Dict:
        """Calculate delivery quality scores"""
        if not speech_analysis:
            return {'total': 0, 'components': {}}
        
        pace_analysis = speech_analysis.get('pace_analysis', {})
        pace_variation = pace_analysis.get('pace_variation', 0)
        
        # Pace consistency score (lower variation is better)
        pace_consistency = max(0, 100 - (pace_variation * 10))
        
        # Volume stability (simplified - would use audio analysis in production)
        volume_stability = 80  # Default
        
        components = {
            'pace_consistency': pace_consistency,
            'volume_stability': volume_stability
        }
        
        total = (
            pace_consistency * 0.6 +
            volume_stability * 0.4
        )
        
        return {
            'total': total,
            'components': components
        }
    
    def _calculate_wpm_score(self, wpm: float) -> float:
        """Calculate score for words per minute"""
        ideal_min, ideal_max = self.ideal_ranges['wpm']
        
        if ideal_min <= wpm <= ideal_max:
            return 100
        elif wpm < 100:
            return max(0, wpm)
        elif wpm > 200:
            return max(0, 100 - (wpm - 200) * 0.5)
        else:
            # Linear interpolation outside ideal range
            if wpm < ideal_min:
                return 80 + (wpm - 120) * 1.0  # 120 WPM = 80 points
            else:
                return 100 - (wpm - ideal_max) * 1.0  # 180 WPM = 80 points
    
    def _calculate_filler_score(self, filler_rate: float) -> float:
        """Calculate score for filler words"""
        ideal_min, ideal_max = self.ideal_ranges['filler_words_per_minute']
        
        if filler_rate <= ideal_max:
            return 100
        elif filler_rate <= 10:
            return max(0, 100 - (filler_rate - ideal_max) * 10)
        else:
            return max(0, 50 - (filler_rate - 10) * 5)
    
    def _calculate_pause_score(self, pause_data: Dict, duration: float) -> float:
        """Calculate score for pauses"""
        if duration == 0:
            return 0
        
        total_pause_duration = pause_data.get('total_duration', 0)
        pause_ratio = total_pause_duration / duration
        
        ideal_min, ideal_max = self.ideal_ranges['pause_ratio']
        
        if ideal_min <= pause_ratio <= ideal_max:
            return 100
        elif pause_ratio < ideal_min:
            return 80 + (pause_ratio / ideal_min) * 20
        else:
            return max(0, 100 - ((pause_ratio - ideal_max) / ideal_max) * 100)
    
    def _calculate_repetition_score(self, repetition_data: Dict) -> float:
        """Calculate score for word repetition"""
        repeated_words = repetition_data.get('repeated_words', {})
        total_repetitions = sum(repeated_words.values())
        
        if total_repetitions == 0:
            return 100
        elif total_repetitions <= 5:
            return 80
        elif total_repetitions <= 10:
            return 60
        elif total_repetitions <= 20:
            return 40
        else:
            return 20
    
    def _calculate_grammar_score(self, grammar_data: Dict, word_count: int) -> float:
        """Calculate score for grammar"""
        error_count = grammar_data.get('count', 0)
        
        if word_count == 0:
            return 0
        
        error_rate = error_count / word_count
        
        if error_rate == 0:
            return 100
        elif error_rate <= 0.01:  # 1 error per 100 words
            return 90
        elif error_rate <= 0.02:
            return 80
        elif error_rate <= 0.05:
            return 60
        else:
            return 40
    
    def _calculate_relevance_score(self, transcript: str, topic_keywords: List[str]) -> float:
        """Calculate relevance to topic"""
        if not topic_keywords or not transcript:
            return 50  # Neutral score
        
        # Count occurrences of topic keywords
        keyword_matches = 0
        transcript_words = transcript.lower().split()
        
        for keyword in topic_keywords:
            if keyword.lower() in transcript:
                keyword_matches += 1
        
        # Calculate relevance percentage
        relevance_percentage = (keyword_matches / len(topic_keywords)) * 100
        
        return min(100, relevance_percentage * 1.2)  # Scale slightly
    
    def _calculate_structure_score(self, transcript: str, word_count: int) -> float:
        """Calculate speech structure score"""
        if word_count < 50:
            return 50  # Not enough content
        
        # Simple structure analysis
        sentences = transcript.split('.')
        sentence_count = len([s for s in sentences if len(s.strip()) > 0])
        
        if sentence_count == 0:
            return 50
        
        avg_sentence_length = word_count / sentence_count
        
        # Ideal sentence length: 15-25 words
        if 15 <= avg_sentence_length <= 25:
            return 90
        elif 10 <= avg_sentence_length <= 30:
            return 70
        else:
            return 50
    
    def _calculate_vocabulary_score(self, speech_analysis: Dict) -> float:
        """Calculate vocabulary diversity score"""
        word_count = speech_analysis.get('word_count', 0)
        
        if word_count < 20:
            return 50
        
        # Simple type-token ratio (vocabulary diversity)
        transcript = speech_analysis.get('transcript', '').lower()
        words = [w for w in transcript.split() if len(w) > 2]  # Filter short words
        
        if not words:
            return 50
        
        unique_words = set(words)
        diversity_ratio = len(unique_words) / len(words)
        
        # Convert to score (good diversity: 0.6-0.8)
        if diversity_ratio >= 0.7:
            return 90
        elif diversity_ratio >= 0.5:
            return 70
        elif diversity_ratio >= 0.3:
            return 50
        else:
            return 30
    
    def _get_performance_level(self, score: float) -> str:
        """Convert numerical score to performance level"""
        if score >= 90:
            return "Excellent"
        elif score >= 80:
            return "Very Good"
        elif score >= 70:
            return "Good"
        elif score >= 60:
            return "Satisfactory"
        elif score >= 50:
            return "Needs Improvement"
        else:
            return "Needs Practice"
    
    def _generate_recommendations(self, category_scores: Dict) -> List[str]:
        """Generate improvement recommendations based on lowest scores"""
        recommendations = []
        
        # Find weakest categories (score < 70)
        weak_categories = []
        for category, data in category_scores.items():
            if data['total'] < 70:
                weak_categories.append((category, data['total']))
        
        # Sort by lowest score
        weak_categories.sort(key=lambda x: x[1])
        
        # Generate recommendations for top 3 weakest categories
        for category, score in weak_categories[:3]:
            if category == 'posture':
                recommendations.append(
                    "💪 Practice maintaining better posture. Sit up straight and keep shoulders relaxed."
                )
            elif category == 'eye_contact':
                recommendations.append(
                    "👀 Improve eye contact by looking directly at the camera more frequently."
                )
            elif category == 'speech':
                recommendations.append(
                    "🗣️ Work on speech clarity. Reduce filler words and practice pacing."
                )
            elif category == 'content':
                recommendations.append(
                    "🎯 Focus on staying relevant to your topic. Use more topic-specific keywords."
                )
            elif category == 'delivery':
                recommendations.append(
                    "🎭 Vary your speaking pace and volume to make your delivery more engaging."
                )
        
        # Add general positive feedback if all scores are good
        if not weak_categories and any(data['total'] >= 80 for data in category_scores.values()):
            recommendations.append(
                "✅ Great overall performance! Continue practicing to maintain these skills."
            )
        
        return recommendations[:3]  # Limit to 3 recommendations
    
    def _get_empty_score(self) -> Dict:
        """Return empty score structure"""
        return {
            'total': 0,
            'performance_level': 'Needs Practice',
            'category_scores': {},
            'recommendations': ["Start practicing to get your first score!"],
            'breakdown': {
                'posture': 0,
                'eye_contact': 0,
                'speech': 0,
                'content': 0,
                'delivery': 0
            }
        }