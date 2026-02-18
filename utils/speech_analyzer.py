# utils/speech_analyzer.py
import re
import nltk
# import language_tool_python  # Commented out due to download issues
from collections import Counter
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)

class SpeechAnalyzer:
    def __init__(self):
        # Download NLTK data if needed
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt_tab')
        
        # Initialize LanguageTool for grammar checking
        # self.language_tool = language_tool_python.LanguageTool('en-US')  # Commented out
        self.language_tool = None
        
        # Enhanced filler words list
        self.filler_words = [
            'um', 'uh', 'like', 'you know', 'actually', 'basically', 
            'literally', 'so', 'well', 'okay', 'right', 'ah', 'er',
            'just', 'kind of', 'sort of', 'i mean', 'you see', 'anyway',
            'basically', 'seriously', 'honestly', 'anyways', 'alright'
        ]
        
        # Common words to ignore in repetition analysis
        self.common_words = set([
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those',
            'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'
        ])
    
    def analyze_transcript(self, transcript_data: Dict) -> Dict:
        """Comprehensive speech analysis from transcript data"""
        try:
            if not transcript_data or 'results' not in transcript_data:
                return self._get_empty_analysis()
            
            # Extract transcript text
            transcript_text = self._extract_transcript_text(transcript_data)
            words = self._extract_words_with_timings(transcript_data)
            
            if not transcript_text.strip():
                return self._get_empty_analysis()
            
            # Perform various analyses
            basic_metrics = self._calculate_basic_metrics(words, transcript_text)
            filler_analysis = self._analyze_filler_words(words)
            pause_analysis = self._analyze_pauses(words)
            repetition_analysis = self._analyze_repetition(words)
            grammar_analysis = self._analyze_grammar(transcript_text)
            pace_analysis = self._analyze_speech_pace(words)
            
            # Combine all analyses
            analysis = {
                **basic_metrics,
                'filler_words': filler_analysis,
                'pauses': pause_analysis,
                'repetition': repetition_analysis,
                'grammar_errors': grammar_analysis,
                'pace_analysis': pace_analysis,
                'transcript': transcript_text,
                'word_timings': words
            }
            
            logger.info(f"Speech analysis completed: {basic_metrics['word_count']} words")
            return analysis
            
        except Exception as e:
            logger.error(f"Speech analysis error: {str(e)}")
            return self._get_empty_analysis()
    
    def _extract_transcript_text(self, transcript_data: Dict) -> str:
        """Extract transcript text from Deepgram response"""
        try:
            channels = transcript_data.get('results', {}).get('channels', [])
            if not channels:
                return ""
            
            alternatives = channels[0].get('alternatives', [])
            if not alternatives:
                return ""
            
            return alternatives[0].get('transcript', "").strip()
            
        except Exception as e:
            logger.error(f"Transcript extraction error: {str(e)}")
            return ""
    
    def _extract_words_with_timings(self, transcript_data: Dict) -> List[Dict]:
        """Extract words with their timings"""
        try:
            channels = transcript_data.get('results', {}).get('channels', [])
            if not channels:
                return []
            
            alternatives = channels[0].get('alternatives', [])
            if not alternatives:
                return []
            
            words = alternatives[0].get('words', [])
            return words
            
        except Exception as e:
            logger.error(f"Word extraction error: {str(e)}")
            return []
    
    def _calculate_basic_metrics(self, words: List[Dict], transcript: str) -> Dict:
        """Calculate basic speech metrics"""
        word_count = len(words)
        
        # Calculate duration
        if words:
            start_time = words[0]['start']
            end_time = words[-1]['end']
            duration = end_time - start_time
        else:
            duration = 0
        
        # Calculate words per minute
        wpm = (word_count / duration * 60) if duration > 0 else 0
        
        # Calculate speaking time (excluding pauses)
        speaking_time = sum(word['end'] - word['start'] for word in words) if words else 0
        
        return {
            'word_count': word_count,
            'duration_seconds': round(duration, 2),
            'words_per_minute': round(wpm),
            'speaking_time_seconds': round(speaking_time, 2),
            'pause_time_seconds': round(duration - speaking_time, 2)
        }
    
    def _analyze_filler_words(self, words: List[Dict]) -> Dict:
        """Analyze filler word usage"""
        filler_counts = Counter()
        total_fillers = 0
        filler_instances = []
        
        for i, word_obj in enumerate(words):
            word = word_obj['word'].lower().strip('.,!?;')
            
            if word in self.filler_words:
                filler_counts[word] += 1
                total_fillers += 1
                
                filler_instances.append({
                    'word': word,
                    'timestamp': word_obj['start'],
                    'position': i
                })
        
        return {
            'total_count': total_fillers,
            'percentage': round((total_fillers / len(words)) * 100, 2) if words else 0,
            'breakdown': dict(filler_counts),
            'instances': filler_instances
        }
    
    def _analyze_pauses(self, words: List[Dict]) -> Dict:
        """Analyze pauses in speech"""
        pauses = []
        total_pause_duration = 0
        
        for i in range(1, len(words)):
            pause_duration = words[i]['start'] - words[i-1]['end']
            
            if pause_duration > 0.3:  # Consider pauses longer than 300ms
                pauses.append({
                    'start': words[i-1]['end'],
                    'end': words[i]['start'],
                    'duration': round(pause_duration, 2),
                    'previous_word': words[i-1]['word'],
                    'next_word': words[i]['word']
                })
                total_pause_duration += pause_duration
        
        avg_pause_duration = total_pause_duration / len(pauses) if pauses else 0
        
        return {
            'count': len(pauses),
            'total_duration': round(total_pause_duration, 2),
            'average_duration': round(avg_pause_duration, 2),
            'details': pauses
        }
    
    def _analyze_repetition(self, words: List[Dict]) -> Dict:
        """Analyze word repetition patterns"""
        # Filter out common words and short words
        content_words = [
            word_obj['word'].lower().strip('.,!?;')
            for word_obj in words
            if (len(word_obj['word']) > 3 and 
                word_obj['word'].lower() not in self.common_words)
        ]
        
        word_freq = Counter(content_words)
        repeated_words = {
            word: count for word, count in word_freq.items()
            if count >= 3  # Words repeated 3+ times
        }
        
        # Find repetition sequences
        repetition_sequences = self._find_repetition_sequences(words)
        
        return {
            'repeated_words': repeated_words,
            'top_repetitions': dict(Counter(repeated_words).most_common(10)),
            'repetition_sequences': repetition_sequences
        }
    
    def _find_repetition_sequences(self, words: List[Dict]) -> List[Dict]:
        """Find sequences where words are repeated consecutively"""
        sequences = []
        i = 0
        
        while i < len(words) - 1:
            current_word = words[i]['word'].lower()
            j = i + 1
            repetition_count = 1
            
            while (j < len(words) and 
                   words[j]['word'].lower() == current_word and
                   words[j]['start'] - words[j-1]['end'] < 2.0):  # Within 2 seconds
                repetition_count += 1
                j += 1
            
            if repetition_count >= 2:  # At least 2 consecutive repetitions
                sequences.append({
                    'word': current_word,
                    'count': repetition_count,
                    'start_time': words[i]['start'],
                    'end_time': words[j-1]['end'],
                    'duration': words[j-1]['end'] - words[i]['start']
                })
                i = j
            else:
                i += 1
        
        return sequences
    
    def _analyze_grammar(self, text: str) -> Dict:
        """Simple grammar analysis without LanguageTool"""
        # Basic grammar checks without LanguageTool
        errors = []
        
        # Check for basic issues
        sentences = text.split('.')
        for i, sentence in enumerate(sentences):
            sentence = sentence.strip()
            if sentence:
                # Check if sentence starts with capital letter
                if not sentence[0].isupper():
                    errors.append({
                        'error': 'Sentence should start with capital letter',
                        'context': sentence[:50],
                        'offset': 0,
                        'suggestions': [sentence.capitalize()],
                        'category': 'Capitalization'
                    })
        
        return {
            'count': len(errors),
            'details': errors
        }
    
    def _analyze_speech_pace(self, words: List[Dict]) -> Dict:
        """Analyze speech pace variations"""
        if len(words) < 2:
            return {'pace_variation': 0, 'pace_segments': []}
        
        # Calculate pace in words per minute for each 10-second segment
        segment_duration = 10  # seconds
        pace_segments = []
        
        if words:
            total_duration = words[-1]['end'] - words[0]['start']
            num_segments = int(total_duration / segment_duration) + 1
            
            for seg in range(num_segments):
                seg_start = words[0]['start'] + seg * segment_duration
                seg_end = seg_start + segment_duration
                
                # Count words in this segment
                seg_words = [
                    w for w in words 
                    if w['start'] >= seg_start and w['end'] <= seg_end
                ]
                
                seg_wpm = len(seg_words) / (segment_duration / 60)
                pace_segments.append({
                    'segment': seg,
                    'start_time': seg_start,
                    'end_time': seg_end,
                    'wpm': round(seg_wpm),
                    'word_count': len(seg_words)
                })
        
        # Calculate pace variation
        wpm_values = [seg['wpm'] for seg in pace_segments if seg['wpm'] > 0]
        pace_variation = np.std(wpm_values) if wpm_values else 0
        
        return {
            'pace_variation': round(pace_variation, 2),
            'pace_segments': pace_segments,
            'recommended_pace_range': (140, 160)
        }
    
    def _get_empty_analysis(self) -> Dict:
        """Return empty analysis structure"""
        return {
            'word_count': 0,
            'duration_seconds': 0,
            'words_per_minute': 0,
            'speaking_time_seconds': 0,
            'pause_time_seconds': 0,
            'filler_words': {
                'total_count': 0,
                'percentage': 0,
                'breakdown': {},
                'instances': []
            },
            'pauses': {
                'count': 0,
                'total_duration': 0,
                'average_duration': 0,
                'details': []
            },
            'repetition': {
                'repeated_words': {},
                'top_repetitions': {},
                'repetition_sequences': []
            },
            'grammar_errors': {
                'count': 0,
                'details': []
            },
            'pace_analysis': {
                'pace_variation': 0,
                'pace_segments': [],
                'recommended_pace_range': (140, 160)
            },
            'transcript': "",
            'word_timings': []
        }

# Import numpy for pace analysis
import numpy as np