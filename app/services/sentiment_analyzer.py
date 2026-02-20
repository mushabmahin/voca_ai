import structlog
from typing import Dict, List, Optional, Tuple
import re
from app.services.ai_client import get_ai_client
from app.models.schemas import SentimentLabel, EmotionLabel, SentimentAnalysis

logger = structlog.get_logger()

class SentimentAnalyzer:
    """
    Service for analyzing sentiment and emotions in conversations.
    Supports multilingual analysis with confidence scoring.
    """
    
    def __init__(self):
        self.ai_client = get_ai_client()
        
        # Sentiment lexicons for different languages
        self.sentiment_lexicons = {
            'en': {
                'positive': ['good', 'great', 'excellent', 'happy', 'satisfied', 'thank', 'appreciate', 'perfect', 'wonderful', 'amazing'],
                'negative': ['bad', 'terrible', 'awful', 'angry', 'frustrated', 'disappointed', 'unhappy', 'worst', 'horrible', 'hate'],
                'neutral': ['okay', 'fine', 'normal', 'regular', 'standard', 'average']
            },
            'es': {
                'positive': ['bueno', 'excelente', 'feliz', 'gracias', 'aprecio', 'perfecto', 'maravilloso', 'increíble'],
                'negative': ['malo', 'terrible', 'horrible', 'enojado', 'frustrado', 'decepcionado', 'infeliz', 'peor'],
                'neutral': ['está bien', 'normal', 'regular', 'estándar', 'promedio']
            },
            'hi': {
                'positive': ['अच्छा', 'बहुत बढ़िया', 'खुश', 'धन्यवाद', 'सराहना', 'पूर्ण', 'अद्भुत'],
                'negative': ['बुरा', 'भयानक', 'गुस्सा', 'निराश', 'दुखी', 'सबसे बुरा'],
                'neutral': ['ठीक है', 'सामान्य', 'रेगुलर', 'औसत']
            }
        }
        
        # Emotion keywords
        self.emotion_keywords = {
            'joy': ['happy', 'excited', 'delighted', 'pleased', 'cheerful', 'glad', 'joyful', 'enthusiastic'],
            'anger': ['angry', 'furious', 'irritated', 'annoyed', 'frustrated', 'mad', 'outraged', 'resentful'],
            'fear': ['scared', 'afraid', 'worried', 'anxious', 'nervous', 'terrified', 'concerned', 'apprehensive'],
            'sadness': ['sad', 'depressed', 'disappointed', 'upset', 'unhappy', 'miserable', 'devastated', 'heartbroken'],
            'surprise': ['surprised', 'shocked', 'amazed', 'astonished', 'stunned', 'bewildered', 'confused'],
            'disgust': ['disgusted', 'revolted', 'repulsed', 'sickened', 'nauseated', 'appalled']
        }
    
    async def analyze_sentiment(
        self,
        text: str,
        language: str = "en",
        enable_timeline: bool = False,
        chunk_size: int = 100
    ) -> SentimentAnalysis:
        """
        Analyze sentiment and emotions in the given text.
        
        Args:
            text: Text to analyze
            language: Language code (ISO 639-1)
            enable_timeline: Whether to generate timeline analysis
            chunk_size: Size of chunks for timeline analysis
            
        Returns:
            SentimentAnalysis object with sentiment, emotions, and optional timeline
        """
        try:
            if not text or len(text.strip()) < 5:
                return SentimentAnalysis(
                    label=SentimentLabel.NEUTRAL,
                    confidence=0.5,
                    emotions=[{"neutral": 0.8}]
                )
            
            # Perform AI-powered sentiment analysis
            sentiment_result = await self._analyze_with_ai(text, language)
            
            # Validate and enhance with rule-based analysis
            enhanced_result = self._enhance_with_rules(sentiment_result, text, language)
            
            # Generate timeline if requested
            timeline = None
            if enable_timeline:
                timeline = await self._generate_timeline(text, language, chunk_size)
            
            logger.info(
                "Sentiment analysis completed",
                sentiment=enhanced_result["label"],
                confidence=enhanced_result["confidence"],
                language=language
            )
            
            return SentimentAnalysis(
                label=SentimentLabel(enhanced_result["label"]),
                confidence=enhanced_result["confidence"],
                emotions=enhanced_result["emotions"],
                timeline=timeline
            )
            
        except Exception as e:
            logger.error("Sentiment analysis failed", error=str(e), exc_info=True)
            # Fallback to rule-based analysis
            return self._fallback_analysis(text, language)
    
    async def _analyze_with_ai(self, text: str, language: str) -> Dict:
        """
        Perform sentiment analysis using OpenAI's language model.
        """
        prompt = self._build_sentiment_prompt(text, language)
        
        try:
            response = await self.ai_client.chat_completion(
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert sentiment analyst. Analyze the emotional tone of conversations and provide structured sentiment analysis."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=200,
                temperature=0.1  # Low temperature for consistent analysis
            )
            
            result_text = response.strip()
            return self._parse_ai_response(result_text)
            
        except Exception as e:
            logger.error("AI sentiment analysis failed", error=str(e))
            raise
    
    def _build_sentiment_prompt(self, text: str, language: str) -> str:
        """
        Build prompt for AI sentiment analysis.
        """
        language_name = self._get_language_name(language)
        
        prompt = f"""
Analyze the sentiment and emotions in this {language_name} conversation text.

Text: {text}

Provide analysis in this exact JSON format:
{{
    "label": "positive|negative|neutral",
    "confidence": 0.0-1.0,
    "emotions": [
        {{"joy": 0.0-1.0}},
        {{"anger": 0.0-1.0}},
        {{"fear": 0.0-1.0}},
        {{"sadness": 0.0-1.0}},
        {{"surprise": 0.0-1.0}},
        {{"disgust": 0.0-1.0}},
        {{"neutral": 0.0-1.0}}
    ]
}}

Requirements:
- label: Overall sentiment (positive, negative, or neutral)
- confidence: Confidence score for the sentiment label (0.0 to 1.0)
- emotions: List of emotion scores, each should sum to approximately 1.0 across all emotions
- Consider the context and nuance of the conversation
- Focus on the dominant emotional tone

JSON Response:
"""
        
        return prompt
    
    def _parse_ai_response(self, response_text: str) -> Dict:
        """
        Parse AI response into structured format.
        """
        try:
            import json
            result = json.loads(response_text)
            
            # Validate required fields
            if "label" not in result or "confidence" not in result or "emotions" not in result:
                raise ValueError("Missing required fields in AI response")
            
            # Validate sentiment label
            valid_labels = ["positive", "negative", "neutral"]
            if result["label"] not in valid_labels:
                result["label"] = "neutral"
            
            # Validate confidence
            if not isinstance(result["confidence"], (int, float)) or not (0 <= result["confidence"] <= 1):
                result["confidence"] = 0.5
            
            # Validate emotions
            if not isinstance(result["emotions"], list):
                result["emotions"] = [{"neutral": 0.8}]
            
            return result
            
        except Exception as e:
            logger.error("Failed to parse AI response", error=str(e))
            # Return default response
            return {
                "label": "neutral",
                "confidence": 0.5,
                "emotions": [{"neutral": 0.8}]
            }
    
    def _enhance_with_rules(self, ai_result: Dict, text: str, language: str) -> Dict:
        """
        Enhance AI analysis with rule-based validation and adjustment.
        """
        text_lower = text.lower()
        
        # Get language-specific lexicon
        lexicon = self.sentiment_lexicons.get(language, self.sentiment_lexicons['en'])
        
        # Count sentiment keywords
        positive_count = sum(1 for word in lexicon['positive'] if word in text_lower)
        negative_count = sum(1 for word in lexicon['negative'] if word in text_lower)
        neutral_count = sum(1 for word in lexicon['neutral'] if word in text_lower)
        
        # Rule-based sentiment
        if positive_count > negative_count and positive_count > neutral_count:
            rule_sentiment = "positive"
        elif negative_count > positive_count and negative_count > neutral_count:
            rule_sentiment = "negative"
        else:
            rule_sentiment = "neutral"
        
        # Adjust AI confidence based on keyword evidence
        keyword_evidence = max(positive_count, negative_count, neutral_count)
        if keyword_evidence > 0:
            # If AI and rules agree, increase confidence
            if ai_result["label"] == rule_sentiment:
                ai_result["confidence"] = min(1.0, ai_result["confidence"] + 0.1)
            else:
                # If they disagree, reduce confidence and consider rule-based result
                ai_result["confidence"] = max(0.3, ai_result["confidence"] - 0.2)
                if ai_result["confidence"] < 0.5:
                    ai_result["label"] = rule_sentiment
        
        # Enhance emotions with keyword matching
        enhanced_emotions = ai_result["emotions"].copy()
        for emotion_dict in enhanced_emotions:
            for emotion, score in emotion_dict.items():
                if emotion in self.emotion_keywords:
                    emotion_words = self.emotion_keywords[emotion]
                    emotion_count = sum(1 for word in emotion_words if word in text_lower)
                    if emotion_count > 0:
                        # Boost emotion score based on keyword evidence
                        emotion_dict[emotion] = min(1.0, score + (emotion_count * 0.1))
        
        return ai_result
    
    async def _generate_timeline(self, text: str, language: str, chunk_size: int) -> List[Dict]:
        """
        Generate timeline-based sentiment analysis.
        """
        try:
            words = text.split()
            chunks = []
            
            # Split text into chunks
            for i in range(0, len(words), chunk_size):
                chunk = ' '.join(words[i:i + chunk_size])
                if len(chunk.strip()) > 5:
                    chunks.append(chunk)
            
            timeline = []
            for i, chunk in enumerate(chunks):
                chunk_analysis = await self._analyze_with_ai(chunk, language)
                
                timeline.append({
                    "segment": i + 1,
                    "start_word": i * chunk_size,
                    "end_word": min((i + 1) * chunk_size, len(words)),
                    "sentiment": chunk_analysis["label"],
                    "confidence": chunk_analysis["confidence"],
                    "dominant_emotion": self._get_dominant_emotion(chunk_analysis["emotions"])
                })
            
            return timeline
            
        except Exception as e:
            logger.error("Timeline generation failed", error=str(e))
            return []
    
    def _get_dominant_emotion(self, emotions: List[Dict]) -> str:
        """
        Get the dominant emotion from emotion scores.
        """
        if not emotions:
            return "neutral"
        
        max_score = 0
        dominant_emotion = "neutral"
        
        for emotion_dict in emotions:
            for emotion, score in emotion_dict.items():
                if score > max_score:
                    max_score = score
                    dominant_emotion = emotion
        
        return dominant_emotion
    
    def _fallback_analysis(self, text: str, language: str) -> SentimentAnalysis:
        """
        Fallback rule-based sentiment analysis.
        """
        text_lower = text.lower()
        lexicon = self.sentiment_lexicons.get(language, self.sentiment_lexicons['en'])
        
        positive_count = sum(1 for word in lexicon['positive'] if word in text_lower)
        negative_count = sum(1 for word in lexicon['negative'] if word in text_lower)
        neutral_count = sum(1 for word in lexicon['neutral'] if word in text_lower)
        
        if positive_count > negative_count and positive_count > neutral_count:
            label = SentimentLabel.POSITIVE
            confidence = min(0.8, 0.5 + (positive_count * 0.1))
        elif negative_count > positive_count and negative_count > neutral_count:
            label = SentimentLabel.NEGATIVE
            confidence = min(0.8, 0.5 + (negative_count * 0.1))
        else:
            label = SentimentLabel.NEUTRAL
            confidence = 0.6
        
        return SentimentAnalysis(
            label=label,
            confidence=confidence,
            emotions=[{"neutral": 0.7}]
        )
    
    def _get_language_name(self, language_code: str) -> str:
        """
        Get full language name from ISO code.
        """
        language_names = {
            'en': 'English',
            'es': 'Spanish',
            'fr': 'French',
            'de': 'German',
            'it': 'Italian',
            'pt': 'Portuguese',
            'hi': 'Hindi',
            'bn': 'Bengali',
            'ta': 'Tamil',
            'te': 'Telugu',
            'zh': 'Chinese',
            'ja': 'Japanese',
            'ko': 'Korean',
            'ar': 'Arabic',
            'ru': 'Russian'
        }
        return language_names.get(language_code, language_code.upper())
