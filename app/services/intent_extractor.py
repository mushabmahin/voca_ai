import structlog
from typing import List, Dict, Optional, Tuple
import re
from app.services.ai_client import get_ai_client
from app.models.schemas import Intent, EntityType, Entity

logger = structlog.get_logger()

class IntentExtractor:
    """
    Service for extracting intents, topics, and entities from conversations.
    Supports industry-specific intent classification and custom entity types.
    """
    
    def __init__(self):
        self.ai_client = get_ai_client()
        
        # Industry-specific intent categories
        self.industry_intents = {
            "banking": [
                "balance_inquiry", "transaction_dispute", "loan_application", "account_opening",
                "fraud_report", "card_issue", "payment_problem", "investment_inquiry",
                "mortgage_inquiry", "credit_card_issue", "online_banking_help", "branch_services"
            ],
            "telecom": [
                "service_outage", "billing_inquiry", "plan_change", "technical_support",
                "network_issue", "device_problem", "account_management", "new_service",
                "portability_request", "complaint", "upgrade_request", "cancellation_request"
            ],
            "fintech": [
                "app_issue", "payment_failure", "account_verification", "transaction_limit",
                "security_concern", "feature_inquiry", "integration_help", "api_support",
                "onboarding_help", "pricing_inquiry", "compliance_question", "bug_report"
            ],
            "bpo": [
                "customer_complaint", "service_request", "escalation", "process_inquiry",
                "quality_issue", "training_request", "policy_question", "system_access",
                "performance_review", "scheduling", "resource_request", "documentation"
            ],
            "general": [
                "information_request", "complaint", "compliment", "appointment",
                "cancellation", "rescheduling", "technical_issue", "billing_inquiry",
                "general_inquiry", "follow_up", "escalation", "feedback"
            ]
        }
        
        # Entity patterns and keywords
        self.entity_patterns = {
            EntityType.PERSON: [
                r'\b(Mr|Mrs|Ms|Dr|Prof)\s+[A-Z][a-z]+\s+[A-Z][a-z]+\b',
                r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b'
            ],
            EntityType.ORGANIZATION: [
                r'\b[A-Z][a-z]+\s+(Bank|Company|Corporation|Inc|Ltd|LLC|Services|Solutions)\b',
                r'\b[A-Z]{2,}\b'  # All caps organization names
            ],
            EntityType.LOCATION: [
                r'\b[A-Z][a-z]+,\s*[A-Z]{2}\b',  # City, State
                r'\b[A-Z][a-z]+\s+(Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd)\b'
            ],
            EntityType.PRODUCT: [
                r'\b[A-Z][a-z]+\s+(Card|Account|Loan|Plan|Service|Package|Product)\b'
            ],
            EntityType.DATE: [
                r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',  # MM/DD/YYYY
                r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b'
            ],
            EntityType.MONEY: [
                r'\$\d+(?:,\d{3})*(?:\.\d{2})?',  # $1,234.56
                r'\b\d+(?:,\d{3})*(?:\.\d{2})?\s*(?:dollars|USD|cents)\b'
            ],
            EntityType.PHONE: [
                r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
                r'\b\+?1[-.]?\d{3}[-.]?\d{3}[-.]?\d{4}\b'
            ],
            EntityType.EMAIL: [
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            ]
        }
        
        # Common topic keywords
        self.topic_keywords = {
            "billing": ["bill", "invoice", "payment", "charge", "cost", "fee", "price", "amount"],
            "technical": ["technical", "system", "app", "website", "login", "password", "error", "bug"],
            "service": ["service", "support", "help", "assistance", "customer service", "representative"],
            "account": ["account", "profile", "settings", "login", "registration", "verification"],
            "product": ["product", "feature", "functionality", "plan", "package", "subscription"],
            "complaint": ["complaint", "unhappy", "dissatisfied", "terrible", "awful", "wrong", "issue"],
            "compliment": ["happy", "satisfied", "great", "excellent", "wonderful", "thank", "appreciate"]
        }
    
    async def extract_intents_and_entities(
        self,
        text: str,
        language: str = "en",
        industry: Optional[str] = None,
        custom_intents: Optional[List[str]] = None
    ) -> Tuple[List[Intent], Dict[str, List[Entity]]]:
        """
        Extract intents and entities from the given text.
        
        Args:
            text: Text to analyze
            language: Language code (ISO 639-1)
            industry: Industry type for specialized intent classification
            custom_intents: Custom intent categories
            
        Returns:
            Tuple of (intents, entities_by_type)
        """
        try:
            if not text or len(text.strip()) < 10:
                return [], {}
            
            # Get intent categories
            intent_categories = self._get_intent_categories(industry, custom_intents)
            
            # Perform AI-powered extraction
            ai_result = await self._extract_with_ai(text, language, intent_categories)
            
            # Extract entities using rule-based methods
            entities = self._extract_entities(text)
            
            # Validate and enhance results
            validated_intents = self._validate_intents(ai_result["intents"], intent_categories)
            enhanced_entities = self._enhance_entities(entities, text, language)
            
            logger.info(
                "Intent and entity extraction completed",
                intents_count=len(validated_intents),
                entities_count=sum(len(entities) for entities in enhanced_entities.values()),
                language=language,
                industry=industry
            )
            
            return validated_intents, enhanced_entities
            
        except Exception as e:
            logger.error("Intent/entity extraction failed", error=str(e), exc_info=True)
            # Fallback to rule-based extraction
            return self._fallback_extraction(text, language, industry)
    
    def _get_intent_categories(self, industry: Optional[str], custom_intents: Optional[List[str]]) -> List[str]:
        """
        Get relevant intent categories based on industry and custom intents.
        """
        if industry and industry in self.industry_intents:
            categories = self.industry_intents[industry].copy()
        else:
            categories = self.industry_intents["general"].copy()
        
        if custom_intents:
            categories.extend(custom_intents)
        
        return categories
    
    async def _extract_with_ai(self, text: str, language: str, intent_categories: List[str]) -> Dict:
        """
        Perform intent and entity extraction using OpenAI.
        """
        prompt = self._build_extraction_prompt(text, language, intent_categories)
        
        try:
            response = await self.ai_client.chat_completion(
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert in conversation analysis. Extract intents, topics, and entities from customer service conversations."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=500,
                temperature=0.2
            )
            
            result_text = response.strip()
            return self._parse_ai_extraction_response(result_text)
            
        except Exception as e:
            logger.error("AI extraction failed", error=str(e))
            raise
    
    def _build_extraction_prompt(self, text: str, language: str, intent_categories: List[str]) -> str:
        """
        Build prompt for AI intent and entity extraction.
        """
        language_name = self._get_language_name(language)
        
        prompt = f"""
Extract intents, topics, and entities from this {language_name} conversation text.

Text: {text}

Available intent categories: {', '.join(intent_categories)}

Provide analysis in this exact JSON format:
{{
    "intents": [
        {{"name": "intent_name", "confidence": 0.0-1.0, "category": "category_name"}}
    ],
    "topics": ["topic1", "topic2", "topic3"],
    "entities": [
        {{"type": "person|organization|location|product|date|money|phone|email|custom", "value": "extracted_value", "confidence": 0.0-1.0}}
    ]
}}

Requirements:
- intents: List 1-3 primary intents with confidence scores
- topics: List main topics discussed
- entities: Extract named entities with confidence scores
- Use only the provided intent categories
- Focus on the most relevant and high-confidence extractions
- Include confidence scores between 0.0 and 1.0

JSON Response:
"""
        
        return prompt
    
    def _parse_ai_extraction_response(self, response_text: str) -> Dict:
        """
        Parse AI extraction response into structured format.
        """
        try:
            import json
            result = json.loads(response_text)
            
            # Validate and set defaults
            if "intents" not in result:
                result["intents"] = []
            if "topics" not in result:
                result["topics"] = []
            if "entities" not in result:
                result["entities"] = []
            
            return result
            
        except Exception as e:
            logger.error("Failed to parse AI extraction response", error=str(e))
            return {"intents": [], "topics": [], "entities": []}
    
    def _extract_entities(self, text: str) -> Dict[str, List[Entity]]:
        """
        Extract entities using rule-based pattern matching.
        """
        entities = {}
        
        for entity_type, patterns in self.entity_patterns.items():
            type_entities = []
            
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                
                for match in matches:
                    entity_value = match.group().strip()
                    
                    # Calculate confidence based on pattern strength
                    confidence = 0.7
                    if entity_type in [EntityType.EMAIL, EntityType.PHONE, EntityType.MONEY]:
                        confidence = 0.9
                    elif entity_type == EntityType.DATE:
                        confidence = 0.8
                    
                    entity = Entity(
                        type=entity_type,
                        value=entity_value,
                        confidence=confidence,
                        start_index=match.start(),
                        end_index=match.end()
                    )
                    
                    type_entities.append(entity)
            
            if type_entities:
                entities[entity_type.value] = type_entities
        
        return entities
    
    def _validate_intents(self, ai_intents: List[Dict], valid_categories: List[str]) -> List[Intent]:
        """
        Validate and filter AI-extracted intents.
        """
        validated_intents = []
        
        for intent_data in ai_intents:
            # Check if intent is in valid categories
            intent_name = intent_data.get("name", "").lower().replace(" ", "_")
            
            if intent_name in valid_categories:
                confidence = intent_data.get("confidence", 0.5)
                
                # Only include intents with reasonable confidence
                if confidence >= 0.3:
                    intent = Intent(
                        name=intent_name,
                        confidence=min(1.0, max(0.0, confidence)),
                        category=intent_data.get("category", "general")
                    )
                    validated_intents.append(intent)
        
        # Sort by confidence and return top 3
        validated_intents.sort(key=lambda x: x.confidence, reverse=True)
        return validated_intents[:3]
    
    def _enhance_entities(self, entities: Dict[str, List[Entity]], text: str, language: str) -> Dict[str, List[Entity]]:
        """
        Enhance entities with additional context and validation.
        """
        enhanced = entities.copy()
        
        # Add topic-based entities
        topics = self._extract_topics(text)
        if topics:
            enhanced["topics"] = [
                Entity(
                    type=EntityType.CUSTOM,
                    value=topic,
                    confidence=0.6
                ) for topic in topics[:5]
            ]
        
        # Remove duplicate entities
        for entity_type in enhanced:
            seen_values = set()
            unique_entities = []
            
            for entity in enhanced[entity_type]:
                if entity.value.lower() not in seen_values:
                    seen_values.add(entity.value.lower())
                    unique_entities.append(entity)
            
            enhanced[entity_type] = unique_entities
        
        return enhanced
    
    def _extract_topics(self, text: str) -> List[str]:
        """
        Extract topics based on keyword matching.
        """
        text_lower = text.lower()
        detected_topics = []
        
        for topic, keywords in self.topic_keywords.items():
            keyword_count = sum(1 for keyword in keywords if keyword in text_lower)
            
            if keyword_count >= 2:  # At least 2 keywords to consider it a topic
                detected_topics.append(topic)
        
        return detected_topics
    
    def _fallback_extraction(self, text: str, language: str, industry: Optional[str]) -> Tuple[List[Intent], Dict[str, List[Entity]]]:
        """
        Fallback rule-based extraction method.
        """
        # Get default intents
        intent_categories = self._get_intent_categories(industry, None)
        
        # Simple keyword-based intent detection
        text_lower = text.lower()
        intents = []
        
        for intent in intent_categories[:10]:  # Limit for performance
            intent_keywords = intent.replace("_", " ")
            if intent_keywords in text_lower:
                intents.append(Intent(
                    name=intent,
                    confidence=0.5,
                    category="general"
                ))
        
        # Extract entities using rule-based method
        entities = self._extract_entities(text)
        
        return intents[:3], entities
    
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
