# -*- coding: utf-8 -*-
"""Test script to verify Gemini AI feedback generation"""

import json
import sys
from utils.gemini_client import GeminiClient

# Sample report data
sample_report = {
    'topic': 'Climate Change Solutions',
    'overall_score': {'total': 75},
    'posture_analysis': {
        'summary': {
            'average_posture_score': 82,
            'average_eye_contact_score': 68,
            'posture_breakdown': {'good_percentage': 70, 'okay_percentage': 20, 'bad_percentage': 10},
            'eye_contact_breakdown': {'good_percentage': 60, 'moderate_percentage': 30, 'poor_percentage': 10}
        }
    },
    'speech_analysis': {
        'words_per_minute': 135,
        'word_count': 450,
        'duration_seconds': 200,
        'filler_words': {'total_count': 8},
        'pauses': {'count': 15},
        'grammar_errors': {'count': 2},
        'transcript': 'Climate change is one of the most pressing issues of our time. We need to take action now to reduce carbon emissions and transition to renewable energy sources.'
    }
}

def test_gemini():
    print("Testing Gemini AI Feedback Generation...")
    print("-" * 60)
    
    # Initialize client
    client = GeminiClient()
    
    if not client.is_available():
        print("[X] Gemini client not available. Check your API key in .env file")
        return
    
    print("[OK] Gemini client initialized successfully")
    print("\nGenerating AI feedback...")
    
    # Generate feedback
    feedback = client.generate_feedback(sample_report)
    
    print("\n" + "=" * 60)
    print("FEEDBACK RESULT:")
    print("=" * 60)
    print(json.dumps(feedback, indent=2))
    
    # Check if it's AI-generated or fallback
    if 'overall_assessment' in feedback:
        assessment = feedback['overall_assessment']
        if 'Your overall performance score is' in assessment:
            print("\n[WARNING] Using FALLBACK feedback (static rules)")
            print("This means Gemini API is not working properly")
        else:
            print("\n[SUCCESS] AI-generated feedback received!")
    
    print("\n" + "=" * 60)

if __name__ == '__main__':
    test_gemini()
