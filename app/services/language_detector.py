import structlog
from typing import List, Dict, Tuple, Optional
from langdetect import detect, detect_langs
from langdetect.lang_detect_exception import LangDetectException
import re

logger = structlog.get_logger()

class LanguageDetector:
    """
    Service for automatic language detection in conversations.
    Supports 30+ languages with confidence scoring.
    """
    
    def __init__(self):
        # Language code to name mapping
        self.language_names = {
            'en': 'English',
            'es': 'Spanish',
            'fr': 'French',
            'de': 'German',
            'it': 'Italian',
            'pt': 'Portuguese',
            'nl': 'Dutch',
            'sv': 'Swedish',
            'da': 'Danish',
            'no': 'Norwegian',
            'hi': 'Hindi',
            'bn': 'Bengali',
            'ta': 'Tamil',
            'te': 'Telugu',
            'mr': 'Marathi',
            'gu': 'Gujarati',
            'kn': 'Kannada',
            'ml': 'Malayalam',
            'pa': 'Punjabi',
            'ur': 'Urdu',
            'zh': 'Chinese',
            'ja': 'Japanese',
            'ko': 'Korean',
            'ar': 'Arabic',
            'ru': 'Russian',
            'tr': 'Turkish',
            'pl': 'Polish',
            'vi': 'Vietnamese',
            'th': 'Thai',
            'id': 'Indonesian'
        }
        
        # Common language indicators for mixed language detection
        self.language_patterns = {
            'hi': [r'\b[कखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसह]+\b'],
            'bn': [r'\b[অআইঈউঊঋএঐওঔকখগঘঙচছজঝঞটঠডঢণতথদধনপফবভমযরলবশষসহ]+\b'],
            'ta': [r'\b[அஆஇஈஉஊஎஏஐஒஓஔகஙசஜஞடணதநபமயரலவழளறன]+\b'],
            'te': [r'\b[అఆఇఈఉఊఋఎఏఐఒఓఔకఖగఘఙచఛజఝఞటఠడఢణతథదధనపఫబభమయరలవశషసహ]+\b'],
            'zh': [r'[\u4e00-\u9fff]+'],
            'ja': [r'[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff]+'],
            'ar': [r'[\u0600-\u06ff]+'],
            'ru': [r'[\u0400-\u04ff]+'],
            'ko': [r'[\uac00-\ud7af]+'],
            'th': [r'[\u0e00-\u0e7f]+']
        }
    
    async def detect_languages(self, text: str, expected_languages: Optional[List[str]] = None) -> Tuple[List[str], Dict[str, float]]:
        """
        Detect languages in the given text.
        
        Args:
            text: Text to analyze
            expected_languages: Optional list of expected languages (ISO codes)
            
        Returns:
            Tuple of (detected_languages, confidence_scores)
        """
        try:
            if not text or len(text.strip()) < 10:
                logger.warning("Text too short for reliable language detection")
                return ['en'], {'en': 0.5}  # Default to English
            
            # Clean text for better detection
            cleaned_text = self._clean_text_for_detection(text)
            
            # Detect primary language(s)
            detected_langs = []
            confidence_scores = {}
            
            try:
                # Use langdetect for primary detection
                lang_probs = detect_langs(cleaned_text)
                
                for lang_prob in lang_probs:
                    lang_code = lang_prob.lang
                    confidence = lang_prob.prob
                    
                    # Only include languages we support
                    if lang_code in self.language_names:
                        detected_langs.append(lang_code)
                        confidence_scores[lang_code] = confidence
                
                # Check for mixed languages using pattern matching
                mixed_langs = self._detect_mixed_languages(text)
                for lang_code in mixed_langs:
                    if lang_code not in detected_langs and lang_code in self.language_names:
                        detected_langs.append(lang_code)
                        confidence_scores[lang_code] = 0.3  # Lower confidence for pattern detection
                
                # Filter by expected languages if provided
                if expected_languages:
                    filtered_langs = []
                    filtered_scores = {}
                    for lang in detected_langs:
                        if lang in expected_languages:
                            filtered_langs.append(lang)
                            filtered_scores[lang] = confidence_scores[lang]
                    
                    if filtered_langs:
                        detected_langs = filtered_langs
                        confidence_scores = filtered_scores
                
                # If no languages detected, default to English
                if not detected_langs:
                    detected_langs = ['en']
                    confidence_scores = {'en': 0.5}
                
                logger.info(
                    "Languages detected",
                    languages=detected_langs,
                    confidence_scores=confidence_scores
                )
                
                return detected_langs, confidence_scores
                
            except LangDetectException as e:
                logger.warning("Language detection failed", error=str(e))
                return ['en'], {'en': 0.5}
                
        except Exception as e:
            logger.error("Language detection error", error=str(e), exc_info=True)
            return ['en'], {'en': 0.5}
    
    def _clean_text_for_detection(self, text: str) -> str:
        """
        Clean text to improve language detection accuracy.
        """
        # Remove URLs, emails, phone numbers, and excessive whitespace
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '', text)
        text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '', text)
        text = re.sub(r'\s+', ' ', text)
        
        # Remove very short words (less than 2 characters)
        words = text.split()
        words = [word for word in words if len(word) > 1]
        
        return ' '.join(words)
    
    def _detect_mixed_languages(self, text: str) -> List[str]:
        """
        Detect presence of specific languages using regex patterns.
        Useful for languages with distinct character sets.
        """
        mixed_langs = []
        
        for lang_code, patterns in self.language_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    mixed_langs.append(lang_code)
                    break
        
        return mixed_langs
    
    def get_language_name(self, lang_code: str) -> str:
        """
        Get full language name from ISO code.
        """
        return self.language_names.get(lang_code, lang_code.upper())
    
    def is_supported_language(self, lang_code: str) -> bool:
        """
        Check if a language is supported.
        """
        return lang_code in self.language_names
    
    def get_supported_languages(self) -> Dict[str, str]:
        """
        Get all supported languages.
        """
        return self.language_names.copy()
    
    async def analyze_language_distribution(self, text: str, chunk_size: int = 500) -> Dict[str, float]:
        """
        Analyze language distribution across text chunks.
        Useful for timeline-based language analysis.
        """
        try:
            words = text.split()
            chunks = []
            
            # Split text into chunks
            for i in range(0, len(words), chunk_size):
                chunk = ' '.join(words[i:i + chunk_size])
                if len(chunk.strip()) > 10:
                    chunks.append(chunk)
            
            language_distribution = {}
            total_chunks = len(chunks)
            
            for chunk in chunks:
                langs, _ = await self.detect_languages(chunk)
                primary_lang = langs[0] if langs else 'en'
                
                if primary_lang not in language_distribution:
                    language_distribution[primary_lang] = 0
                language_distribution[primary_lang] += 1
            
            # Convert to percentages
            for lang in language_distribution:
                language_distribution[lang] = (language_distribution[lang] / total_chunks) * 100
            
            return language_distribution
            
        except Exception as e:
            logger.error("Language distribution analysis failed", error=str(e))
            return {'en': 100.0}
