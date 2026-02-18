# services/topic_extractor.py
import re
import logging
from typing import Dict, List, Optional
from collections import Counter
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.tag import pos_tag

logger = logging.getLogger(__name__)

class TopicExtractor:
    def __init__(self):
        # Download NLTK data if needed
        try:
            nltk.data.find('tokenizers/punkt')
            nltk.data.find('corpora/stopwords')
            nltk.data.find('taggers/averaged_perceptron_tagger_eng')
        except LookupError:
            nltk.download('punkt_tab')
            nltk.download('stopwords')
            nltk.download('averaged_perceptron_tagger_eng')
        
        self.stop_words = set(stopwords.words('english'))
        self.stop_words.update(['would', 'could', 'should', 'may', 'might', 'can', 'will'])
        
        # Common presentation phrases to ignore
        self.presentation_phrases = {
            'thank you', 'hello everyone', 'good morning', 'good afternoon',
            'today i will', 'in this presentation', 'lets talk about',
            'as you can see', 'moving on to', 'in conclusion', 'any questions'
        }
    
    def extract_from_content(self, content: str) -> Dict:
        """Extract main topic and keywords from content"""
        try:
            if not content or not content.strip():
                return self._get_empty_topic_data()
            
            # Preprocess content
            cleaned_content = self._preprocess_content(content)
            
            # Extract sentences and words
            sentences = sent_tokenize(cleaned_content)
            words = word_tokenize(cleaned_content.lower())
            
            # Remove stop words and short words
            filtered_words = [
                word for word in words 
                if (word not in self.stop_words and 
                    len(word) > 2 and 
                    word.isalpha())
            ]
            
            # Extract key phrases and keywords
            key_phrases = self._extract_key_phrases(sentences)
            keywords = self._extract_keywords(filtered_words)
            
            # Determine main topic
            main_topic = self._determine_main_topic(key_phrases, keywords, sentences)
            
            return {
                'main_topic': main_topic,
                'keywords': keywords[:10],  # Top 10 keywords
                'key_phrases': key_phrases[:5],  # Top 5 phrases
                'content_length': len(content),
                'sentence_count': len(sentences),
                'word_count': len(filtered_words)
            }
            
        except Exception as e:
            logger.error(f"Topic extraction error: {str(e)}")
            return self._get_empty_topic_data()
    
    def extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text"""
        try:
            if not text or not text.strip():
                return []
            
            # Preprocess text
            cleaned_text = self._preprocess_content(text)
            words = word_tokenize(cleaned_text.lower())
            
            # Filter words
            filtered_words = [
                word for word in words 
                if (word not in self.stop_words and 
                    len(word) > 2 and 
                    word.isalpha())
            ]
            
            # Extract keywords using frequency and POS
            keywords = self._extract_keywords_from_words(filtered_words)
            
            return keywords[:15]  # Return top 15 keywords
            
        except Exception as e:
            logger.error(f"Keyword extraction error: {str(e)}")
            return []
    
    def _preprocess_content(self, content: str) -> str:
        """Preprocess content for analysis"""
        # Remove extra whitespace
        content = re.sub(r'\s+', ' ', content)
        
        # Remove common presentation phrases
        for phrase in self.presentation_phrases:
            content = re.sub(re.escape(phrase), '', content, flags=re.IGNORECASE)
        
        # Remove special characters but keep basic punctuation
        content = re.sub(r'[^\w\s.,!?;]', '', content)
        
        return content.strip()
    
    def _extract_key_phrases(self, sentences: List[str]) -> List[str]:
        """Extract key phrases from sentences"""
        phrases = []
        
        for sentence in sentences:
            # Simple noun phrase extraction
            words = word_tokenize(sentence)
            tagged_words = pos_tag(words)
            
            # Extract noun phrases (sequences of nouns)
            current_phrase = []
            for word, tag in tagged_words:
                if tag.startswith('NN'):  # Noun
                    current_phrase.append(word)
                else:
                    if len(current_phrase) >= 2:  # At least 2 words
                        phrases.append(' '.join(current_phrase))
                    current_phrase = []
            
            # Don't forget the last phrase
            if len(current_phrase) >= 2:
                phrases.append(' '.join(current_phrase))
        
        # Count phrase frequency
        phrase_counts = Counter(phrases)
        return [phrase for phrase, count in phrase_counts.most_common(10)]
    
    def _extract_keywords(self, words: List[str]) -> List[str]:
        """Extract keywords from word list"""
        # Count word frequency
        word_counts = Counter(words)
        
        # Filter out words that appear only once (if we have enough data)
        if len(word_counts) > 20:
            keywords = [(word, count) for word, count in word_counts.items() if count > 1]
        else:
            keywords = list(word_counts.items())
        
        # Sort by frequency
        keywords.sort(key=lambda x: x[1], reverse=True)
        
        return [word for word, count in keywords[:20]]
    
    def _extract_keywords_from_words(self, words: List[str]) -> List[str]:
        """Extract keywords using POS tagging and frequency"""
        if not words:
            return []
        
        # POS tagging to focus on nouns and adjectives
        tagged_words = pos_tag(words)
        
        # Filter for nouns and adjectives
        content_words = [
            word for word, tag in tagged_words 
            if tag.startswith(('NN', 'JJ'))  # Nouns and adjectives
        ]
        
        # Count frequency
        word_counts = Counter(content_words)
        
        # Return most frequent content words
        return [word for word, count in word_counts.most_common(15)]
    
    def _determine_main_topic(self, key_phrases: List[str], 
                            keywords: List[str], 
                            sentences: List[str]) -> str:
        """Determine the main topic from extracted information"""
        if not sentences:
            return "General Presentation"
        
        # Use the first sentence as potential topic
        first_sentence = sentences[0].strip()
        
        # If first sentence is very short, it might be a title
        if (len(first_sentence) < 100 and 
            not first_sentence.lower().startswith(('thank', 'hello', 'good'))):
            return first_sentence
        
        # Otherwise, use the most frequent key phrase
        if key_phrases:
            return key_phrases[0]
        
        # Or use top keywords to form a topic
        if keywords:
            return " ".join(keywords[:3]).title()
        
        # Fallback: use beginning of first meaningful sentence
        for sentence in sentences:
            clean_sentence = sentence.strip()
            if (len(clean_sentence) > 20 and 
                not clean_sentence.lower().startswith(('thank', 'hello', 'good'))):
                words = clean_sentence.split()[:5]  # First 5 words
                return " ".join(words) + "..."
        
        return "Presentation Topic"
    
    def _get_empty_topic_data(self) -> Dict:
        """Return empty topic data structure"""
        return {
            'main_topic': 'General Presentation',
            'keywords': [],
            'key_phrases': [],
            'content_length': 0,
            'sentence_count': 0,
            'word_count': 0
        }