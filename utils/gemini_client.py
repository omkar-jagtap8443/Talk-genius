# utils/gemini_client.py
import google.generativeai as genai
import json
import logging
import re
from typing import Dict, List, Optional
import markdown
from config import Config

logger = logging.getLogger(__name__)

class GeminiClient:
    def __init__(self):
        self.api_key = Config.GEMINI_API_KEY
        self.model_name = "gemini-1.5-flash-latest"
        self.model = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Gemini client"""
        try:
            if not self.api_key or self.api_key == 'your-gemini-api-key':
                logger.warning("Gemini API key not configured")
                return
            
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
            logger.info("Gemini client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {str(e)}")
    
    def generate_feedback(self, report_data: Dict) -> Dict:
        """Generate comprehensive feedback using Gemini"""
        if not self.model:
            return self._get_fallback_feedback(report_data)
        
        try:
            prompt = self._create_feedback_prompt(report_data)
            response = self._call_gemini_api(prompt)
            return self._parse_feedback_response(response, report_data)
            
        except Exception as e:
            logger.error(f"Gemini feedback generation failed: {str(e)}")
            return self._get_fallback_feedback(report_data)
    
    def _create_feedback_prompt(self, report_data: Dict) -> str:
        """Create prompt for Gemini feedback generation"""
        posture_analysis = report_data.get('posture_analysis', {})
        speech_analysis = report_data.get('speech_analysis', {})
        overall_score = report_data.get('overall_score', {})
        topic = report_data.get('topic', 'General Presentation')
        
        # Extract key metrics
        posture_summary = posture_analysis.get('summary', {})
        speech_metrics = {
            'wpm': speech_analysis.get('words_per_minute', 0),
            'filler_words': speech_analysis.get('filler_words', {}).get('total_count', 0),
            'pauses': speech_analysis.get('pauses', {}).get('count', 0),
            'grammar_errors': speech_analysis.get('grammar_errors', {}).get('count', 0),
            'word_count': speech_analysis.get('word_count', 0),
            'duration': speech_analysis.get('duration_seconds', 0)
        }
        
        transcript = speech_analysis.get('transcript', '')[:2000]  # Limit transcript length
        
        prompt = f"""
        As an expert speech coach, provide comprehensive, actionable feedback for this practice session.

        TOPIC: "{topic}"
        DURATION: {speech_metrics['duration']} seconds
        WORD COUNT: {speech_metrics['word_count']} words

        PERFORMANCE METRICS:
        - Overall Score: {overall_score.get('total', 0)}/100
        - Words Per Minute: {speech_metrics['wpm']} (Ideal: 140-160)
        - Filler Words: {speech_metrics['filler_words']}
        - Pauses: {speech_metrics['pauses']}
        - Grammar Errors: {speech_metrics['grammar_errors']}
        - Posture Score: {posture_summary.get('average_posture_score', 0)}%
        - Eye Contact Score: {posture_summary.get('average_eye_contact_score', 0)}%

        POSTURE BREAKDOWN:
        - Good Posture: {posture_summary.get('posture_breakdown', {}).get('good_percentage', 0)}%
        - Okay Posture: {posture_summary.get('posture_breakdown', {}).get('okay_percentage', 0)}%
        - Poor Posture: {posture_summary.get('posture_breakdown', {}).get('bad_percentage', 0)}%

        EYE CONTACT BREAKDOWN:
        - Good Eye Contact: {posture_summary.get('eye_contact_breakdown', {}).get('good_percentage', 0)}%
        - Moderate Eye Contact: {posture_summary.get('eye_contact_breakdown', {}).get('moderate_percentage', 0)}%
        - Poor Eye Contact: {posture_summary.get('eye_contact_breakdown', {}).get('poor_percentage', 0)}%

        TRANSCRIPT (excerpt):
        "{transcript}"

        Please provide feedback in this exact JSON format:
        {{
            "overall_assessment": "Brief overall assessment (2-3 sentences)",
            "strengths": [
                "3 specific strengths based on the data",
                "Focus on what was done well",
                "Be specific and encouraging"
            ],
            "areas_for_improvement": [
                "3 specific areas needing improvement",
                "Provide actionable advice",
                "Be constructive, not critical"
            ],
            "personalized_exercises": [
                "2 personalized practice exercises",
                "Make them relevant to the weaknesses identified",
                "Include time estimates if possible"
            ],
            "delivery_tips": [
                "2 specific delivery improvement tips",
                "Focus on immediate improvements",
                "Make them easy to implement"
            ],
            "topic_relevance_feedback": "Specific feedback on how well they addressed the topic",
            "confidence_rating": 8,
            "next_steps": "What to focus on in the next practice session"
        }}

        Guidelines:
        - Be specific and data-driven
        - Focus on actionable advice
        - Balance positive reinforcement with constructive criticism
        - Consider the topic and context
        - Make exercises practical and time-bound
        """
        
        return prompt
    
    def _call_gemini_api(self, prompt: str) -> str:
        """Call Gemini API with the given prompt"""
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Gemini API call failed: {str(e)}")
            raise
    
    def _parse_feedback_response(self, response: str, report_data: Dict) -> Dict:
        """Parse Gemini response into structured feedback"""
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                parsed_feedback = json.loads(json_match.group())
                
                # Validate required fields
                required_fields = ['strengths', 'areas_for_improvement', 'personalized_exercises']
                if all(field in parsed_feedback for field in required_fields):
                    return self._enhance_feedback_with_markdown(parsed_feedback)
            
            # If JSON parsing fails, use fallback
            logger.warning("Failed to parse Gemini response as JSON, using fallback")
            return self._get_fallback_feedback(report_data)
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {str(e)}")
            return self._get_fallback_feedback(report_data)
    
    def _enhance_feedback_with_markdown(self, feedback: Dict) -> Dict:
        """Convert feedback to HTML with markdown formatting"""
        html_feedback = {}
        
        for key, value in feedback.items():
            if isinstance(value, str):
                # Convert markdown to HTML
                html_feedback[key] = markdown.markdown(value)
            elif isinstance(value, list):
                # Convert list items to HTML
                html_items = []
                for item in value:
                    if isinstance(item, str):
                        html_items.append(markdown.markdown(f"- {item}"))
                    else:
                        html_items.append(str(item))
                html_feedback[key] = "\n".join(html_items)
            else:
                html_feedback[key] = value
        
        return html_feedback
    
    def _get_fallback_feedback(self, report_data: Dict) -> Dict:
        """Generate fallback feedback when Gemini is unavailable"""
        posture_analysis = report_data.get('posture_analysis', {})
        speech_analysis = report_data.get('speech_analysis', {})
        overall_score = report_data.get('overall_score', {}).get('total', 0)
        
        posture_summary = posture_analysis.get('summary', {})
        speech_metrics = speech_analysis
        
        # Generate feedback based on scores
        strengths = []
        improvements = []
        
        # Posture strengths/improvements
        posture_score = posture_summary.get('average_posture_score', 0)
        if posture_score >= 80:
            strengths.append("Excellent posture throughout your presentation")
        elif posture_score >= 60:
            strengths.append("Good overall posture with room for refinement")
        else:
            improvements.append("Work on maintaining better posture - sit up straight and keep shoulders relaxed")
        
        # Eye contact strengths/improvements
        eye_contact_score = posture_summary.get('average_eye_contact_score', 0)
        if eye_contact_score >= 75:
            strengths.append("Strong eye contact with your audience")
        elif eye_contact_score >= 50:
            improvements.append("Improve eye contact by looking directly at the camera more frequently")
        else:
            improvements.append("Focus on maintaining better eye contact with your audience")
        
        # Speech strengths/improvements
        wpm = speech_metrics.get('words_per_minute', 0)
        if 140 <= wpm <= 160:
            strengths.append("Perfect speaking pace - clear and engaging")
        elif wpm < 120:
            improvements.append("Increase your speaking pace to maintain audience engagement")
        else:
            improvements.append("Slow down slightly for better clarity")
        
        filler_count = speech_metrics.get('filler_words', {}).get('total_count', 0)
        if filler_count <= 3:
            strengths.append("Excellent control of filler words")
        elif filler_count <= 8:
            improvements.append("Reduce filler words by pausing instead of using 'um' or 'like'")
        else:
            improvements.append("Focus on eliminating filler words for more professional delivery")
        
        # Ensure we have at least 3 items each
        while len(strengths) < 3:
            strengths.append("Clear communication and good vocal projection")
        
        while len(improvements) < 3:
            improvements.append("Practice varying your vocal tone to maintain engagement")
        
        return {
            'overall_assessment': f"Your overall performance score is {overall_score}/100. {self._get_overall_comment(overall_score)}",
            'strengths': strengths[:3],
            'areas_for_improvement': improvements[:3],
            'personalized_exercises': [
                "Practice 2-minute speeches while focusing on posture and eye contact",
                "Record yourself and count filler words, aiming to reduce them by 50% each practice",
                "Use a mirror to practice maintaining eye contact while speaking"
            ],
            'delivery_tips': [
                "Use strategic pauses to emphasize key points",
                "Vary your vocal tone to maintain audience engagement"
            ],
            'topic_relevance_feedback': "Good content organization and topic coverage",
            'confidence_rating': min(9, max(1, overall_score // 10)),
            'next_steps': "Focus on your highest priority improvement areas in your next practice session"
        }
    
    def _get_overall_comment(self, score: float) -> str:
        """Get overall comment based on score"""
        if score >= 90:
            return "Outstanding performance! Your delivery is professional and engaging."
        elif score >= 80:
            return "Excellent work! You demonstrate strong presentation skills."
        elif score >= 70:
            return "Good performance with several strengths and some areas for refinement."
        elif score >= 60:
            return "Solid foundation with clear opportunities for improvement."
        else:
            return "Good start! Focus on the key improvement areas to enhance your skills."
    
    def is_available(self) -> bool:
        """Check if Gemini client is available"""
        return self.model is not None
    
    def generate_summary(self, content: str, max_length: int = 500) -> str:
        """Generate summary of content using Gemini"""
        if not self.model or not content:
            return content[:max_length] + "..." if len(content) > max_length else content
        
        try:
            prompt = f"""
            Please provide a concise summary of the following content in {max_length} characters or less:
            
            {content}
            
            Summary:
            """
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Summary generation failed: {str(e)}")
            return content[:max_length] + "..." if len(content) > max_length else content