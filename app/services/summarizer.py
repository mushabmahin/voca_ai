import structlog
from typing import List, Dict, Optional
import re
from app.services.ai_client import get_ai_client

logger = structlog.get_logger()

class ConversationSummarizer:
    """
    Service for generating concise, accurate summaries of conversations.
    Supports multilingual summaries with configurable length.
    """
    
    def __init__(self):
        self.ai_client = get_ai_client()
        
        # Summary templates for different industries
        self.industry_templates = {
            "banking": {
                "focus_areas": ["account issues", "loan inquiries", "compliance disclosures", "fraud concerns", "transaction disputes"],
                "key_terms": ["account", "loan", "balance", "transaction", "payment", "fraud", "compliance"]
            },
            "telecom": {
                "focus_areas": ["service outages", "billing issues", "plan changes", "technical support", "network problems"],
                "key_terms": ["service", "outage", "billing", "plan", "network", "connection", "technical"]
            },
            "fintech": {
                "focus_areas": ["app issues", "payment failures", "account verification", "transaction limits", "security"],
                "key_terms": ["app", "payment", "verification", "transaction", "security", "limit", "account"]
            },
            "bpo": {
                "focus_areas": ["customer complaints", "service requests", "escalations", "process issues", "quality concerns"],
                "key_terms": ["complaint", "request", "escalation", "process", "quality", "service", "issue"]
            }
        }
    
    async def generate_summary(
        self,
        text: str,
        language: str = "en",
        target_length: int = 100,
        industry: Optional[str] = None,
        custom_focus: Optional[List[str]] = None
    ) -> str:
        """
        Generate a concise summary of the conversation.
        
        Args:
            text: Conversation transcript
            language: Primary language code (ISO 639-1)
            target_length: Target summary length in words
            industry: Industry type for context-aware summarization
            custom_focus: Custom focus areas for the summary
            
        Returns:
            Generated summary string
        """
        try:
            if not text or len(text.strip()) < 20:
                return "Conversation too short for meaningful summary."
            
            # Prepare context for the summary
            context = self._prepare_summary_context(text, language, industry, custom_focus)
            
            # Generate summary using OpenAI
            summary = await self._generate_ai_summary(context, target_length, language)
            
            # Validate summary quality
            validated_summary = self._validate_summary(summary, text, target_length)
            
            logger.info(
                "Summary generated successfully",
                original_length=len(text),
                summary_length=len(validated_summary.split()),
                language=language
            )
            
            return validated_summary
            
        except Exception as e:
            logger.error("Summary generation failed", error=str(e), exc_info=True)
            # Fallback to extractive summary
            return self._generate_extractive_summary(text, target_length)
    
    def _prepare_summary_context(
        self,
        text: str,
        language: str,
        industry: Optional[str],
        custom_focus: Optional[List[str]]
    ) -> Dict:
        """
        Prepare context information for AI-powered summarization.
        """
        context = {
            "text": text,
            "language": language,
            "language_name": self._get_language_name(language),
            "industry": industry,
            "text_length": len(text),
            "word_count": len(text.split())
        }
        
        # Add industry-specific context
        if industry and industry in self.industry_templates:
            template = self.industry_templates[industry]
            context["focus_areas"] = template["focus_areas"]
            context["key_terms"] = template["key_terms"]
        elif custom_focus:
            context["focus_areas"] = custom_focus
            context["key_terms"] = custom_focus
        else:
            context["focus_areas"] = ["main issue", "resolution", "customer sentiment", "key actions"]
            context["key_terms"] = []
        
        # Extract key information
        context.update(self._extract_key_information(text))
        
        return context
    
    async def _generate_ai_summary(self, context: Dict, target_length: int, language: str) -> str:
        """
        Generate summary using OpenAI's language model.
        """
        prompt = self._build_summary_prompt(context, target_length, language)
        
        try:
            response = await self.ai_client.chat_completion(
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": f"Conversation:\n{context['text']}"}
                ],
                temperature=0.3,
                max_tokens=target_length * 2,  # Approximate tokens needed
            )
            
            return response.strip()
            
        except Exception as e:
            logger.error("AI summary generation failed", error=str(e))
            raise
    
    def _build_summary_prompt(self, context: Dict, target_length: int, language: str) -> str:
        """
        Build the prompt for AI summarization.
        """
        language_name = context["language_name"]
        
        prompt = f"""
Generate a {target_length}-word summary of this {language_name} customer service conversation.

Conversation:
{context['text']}

Requirements:
1. Length: Exactly {target_length} words (±10 words acceptable)
2. Language: {language_name}
3. Focus on: {', '.join(context['focus_areas'])}
4. Include: Main issue, resolution status, and customer sentiment
5. Avoid: Hallucinated details, personal information, exact quotes
6. Style: Professional, objective, and concise

"""
        
        if context.get("key_terms"):
            prompt += f"7. Ensure inclusion of relevant terms: {', '.join(context['key_terms'])}\n\n"
        
        prompt += "Summary:"
        
        return prompt
    
    def _validate_summary(self, summary: str, original_text: str, target_length: int) -> str:
        """
        Validate and adjust summary quality.
        """
        if not summary:
            return self._generate_extractive_summary(original_text, target_length)
        
        # Check length
        word_count = len(summary.split())
        if word_count < target_length * 0.5 or word_count > target_length * 2:
            logger.warning(
                "Summary length outside target range",
                target=target_length,
                actual=word_count
            )
        
        # Check for hallucination (basic check)
        original_words = set(original_text.lower().split())
        summary_words = set(summary.lower().split())
        
        # If too many words in summary not in original, it might be hallucinated
        non_original_words = summary_words - original_words
        if len(non_original_words) > len(summary_words) * 0.3:
            logger.warning(
                "Potential hallucination detected in summary",
                non_original_words=len(non_original_words),
                total_summary_words=len(summary_words)
            )
        
        return summary
    
    def _generate_extractive_summary(self, text: str, target_length: int) -> str:
        """
        Fallback extractive summarization method.
        """
        try:
            # Split into sentences
            sentences = re.split(r'[.!?]+', text)
            sentences = [s.strip() for s in sentences if s.strip()]
            
            if not sentences:
                return "Unable to generate summary."
            
            # Score sentences based on length and key terms
            scored_sentences = []
            for i, sentence in enumerate(sentences):
                score = 0
                
                # Prefer medium-length sentences
                words = len(sentence.split())
                if 10 <= words <= 25:
                    score += 2
                elif 5 <= words <= 35:
                    score += 1
                
                # Position importance (first and last sentences)
                if i == 0 or i == len(sentences) - 1:
                    score += 1
                
                # Contains important indicators
                if any(word in sentence.lower() for word in ['problem', 'issue', 'resolve', 'solution', 'help', 'need']):
                    score += 1
                
                scored_sentences.append((score, sentence))
            
            # Sort by score and select top sentences
            scored_sentences.sort(reverse=True, key=lambda x: x[0])
            
            summary_words = 0
            summary_sentences = []
            
            for score, sentence in scored_sentences:
                words = len(sentence.split())
                if summary_words + words <= target_length:
                    summary_sentences.append(sentence)
                    summary_words += words
                else:
                    break
            
            if not summary_sentences:
                return sentences[0][:target_length * 5]  # First sentence truncated
            
            return '. '.join(summary_sentences) + '.'
            
        except Exception as e:
            logger.error("Extractive summarization failed", error=str(e))
            return text[:target_length * 5] + "..." if len(text) > target_length * 5 else text
    
    def _extract_key_information(self, text: str) -> Dict:
        """
        Extract key information from the conversation.
        """
        info = {
            "has_resolution": False,
            "has_complaint": False,
            "has_question": False,
            "sentiment_indicators": []
        }
        
        text_lower = text.lower()
        
        # Check for resolution indicators
        resolution_words = ["resolved", "fixed", "solved", "completed", "done", "sorted"]
        info["has_resolution"] = any(word in text_lower for word in resolution_words)
        
        # Check for complaint indicators
        complaint_words = ["complaint", "unhappy", "dissatisfied", "terrible", "awful", "wrong", "problem"]
        info["has_complaint"] = any(word in text_lower for word in complaint_words)
        
        # Check for question indicators
        info["has_question"] = '?' in text or any(word in text_lower for word in ["question", "how", "what", "why", "when", "where"])
        
        # Extract sentiment indicators
        positive_words = ["happy", "satisfied", "good", "great", "excellent", "thank", "appreciate"]
        negative_words = ["angry", "frustrated", "disappointed", "terrible", "awful", "unhappy"]
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            info["sentiment_indicators"].append("positive")
        elif negative_count > positive_count:
            info["sentiment_indicators"].append("negative")
        else:
            info["sentiment_indicators"].append("neutral")
        
        return info
    
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
