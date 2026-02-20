import structlog
from typing import Dict, List, Optional, Any
import json
import os
from app.models.schemas import RequestConfig

logger = structlog.get_logger()

class ContextEngine:
    """
    Configurable client context engine that applies business rules
    and industry-specific logic to conversation analysis.
    """
    
    def __init__(self):
        self.industry_configs = self._load_industry_configs()
        self.default_config = self._get_default_config()
    
    def _load_industry_configs(self) -> Dict[str, Dict]:
        """
        Load industry-specific configurations.
        """
        return {
            "banking": {
                "compliance_keywords": [
                    "fdic", "disclosure", "verification", "identity", "fraud", "security",
                    "regulation", "compliance", "risk", "audit", "privacy", "consent"
                ],
                "risk_factors": {
                    "missing_disclosure": 0.8,
                    "identity_not_verified": 0.9,
                    "fraud_suspicion": 0.95,
                    "privacy_violation": 0.85,
                    "regulatory_breach": 0.9
                },
                "required_phrases": [
                    "verify your identity", "disclosure", "privacy notice", "terms and conditions"
                ],
                "prohibited_phrases": [
                    "guaranteed approval", "no credit check", "off the books", "under the table"
                ],
                "sentiment_weights": {
                    "negative": 1.2,  # Weight negative sentiment more heavily
                    "positive": 0.8,
                    "neutral": 1.0
                }
            },
            "telecom": {
                "compliance_keywords": [
                    "service_level", "outage", "credit", "billing", "contract", "cancellation",
                    "portability", "roaming", "data_cap", "throttling", "privacy"
                ],
                "risk_factors": {
                    "service_outage": 0.6,
                    "billing_dispute": 0.5,
                    "contract_violation": 0.7,
                    "privacy_concern": 0.6,
                    "service_quality": 0.4
                },
                "required_phrases": [
                    "service agreement", "terms of service", "billing cycle"
                ],
                "prohibited_phrases": [
                    "unlimited guaranteed", "lifetime guarantee", "never fails"
                ],
                "sentiment_weights": {
                    "negative": 1.1,
                    "positive": 0.9,
                    "neutral": 1.0
                }
            },
            "fintech": {
                "compliance_keywords": [
                    "encryption", "authentication", "authorization", "api", "security",
                    "compliance", "regulation", "audit", "data_protection", "pci", "gdpr"
                ],
                "risk_factors": {
                    "security_breach": 0.95,
                    "data_leak": 0.9,
                    "unauthorized_access": 0.85,
                    "compliance_violation": 0.8,
                    "system_failure": 0.7
                },
                "required_phrases": [
                    "two-factor authentication", "encryption", "secure connection"
                ],
                "prohibited_phrases": [
                    "unbreakable security", "100% hackproof", "impossible to breach"
                ],
                "sentiment_weights": {
                    "negative": 1.3,  # Weight negative sentiment heavily in fintech
                    "positive": 0.7,
                    "neutral": 1.0
                }
            },
            "bpo": {
                "compliance_keywords": [
                    "quality", "sla", "kpi", "procedure", "protocol", "training",
                    "compliance", "audit", "performance", "productivity", "escalation"
                ],
                "risk_factors": {
                    "sla_breach": 0.7,
                    "quality_issue": 0.6,
                    "protocol_violation": 0.5,
                    "training_gap": 0.4,
                    "performance_issue": 0.5
                },
                "required_phrases": [
                    "quality assurance", "service level", "standard procedure"
                ],
                "prohibited_phrases": [
                    "skip protocol", "ignore procedure", "bypass security"
                ],
                "sentiment_weights": {
                    "negative": 1.0,
                    "positive": 1.0,
                    "neutral": 1.0
                }
            }
        }
    
    def _get_default_config(self) -> Dict:
        """
        Get default configuration for general use.
        """
        return {
            "compliance_keywords": [
                "help", "support", "service", "issue", "problem", "resolution",
                "satisfaction", "quality", "complaint", "feedback"
            ],
            "risk_factors": {
                "customer_dissatisfaction": 0.5,
                "service_failure": 0.6,
                "communication_issue": 0.4
            },
            "required_phrases": [],
            "prohibited_phrases": [],
            "sentiment_weights": {
                "negative": 1.0,
                "positive": 1.0,
                "neutral": 1.0
            }
        }
    
    def apply_context(
        self,
        analysis_result: Dict,
        config: Optional[RequestConfig] = None,
        text: Optional[str] = None
    ) -> Dict:
        """
        Apply client context and business rules to analysis results.
        
        Args:
            analysis_result: Raw analysis results from AI services
            config: Client configuration
            text: Original conversation text for validation
            
        Returns:
            Enhanced analysis results with context applied
        """
        try:
            # Get effective configuration
            effective_config = self._get_effective_config(config)
            
            # Apply industry-specific rules
            enhanced_result = self._apply_industry_rules(analysis_result, effective_config, text)
            
            # Apply custom business rules
            enhanced_result = self._apply_custom_rules(enhanced_result, config, text)
            
            # Adjust sentiment weights
            enhanced_result = self._apply_sentiment_weights(enhanced_result, effective_config)
            
            # Apply risk threshold
            enhanced_result = self._apply_risk_threshold(enhanced_result, config)
            
            logger.info(
                "Context applied successfully",
                industry=effective_config.get("industry"),
                risk_threshold=config.risk_threshold if config else None
            )
            
            return enhanced_result
            
        except Exception as e:
            logger.error("Context application failed", error=str(e), exc_info=True)
            return analysis_result
    
    def _get_effective_config(self, client_config: Optional[RequestConfig]) -> Dict:
        """
        Get effective configuration by merging client config with industry defaults.
        """
        if not client_config:
            return self.default_config
        
        industry = client_config.industry or "general"
        base_config = self.industry_configs.get(industry, self.default_config).copy()
        
        # Override with client-specific settings
        if client_config.compliance_keywords:
            base_config["compliance_keywords"].extend(client_config.compliance_keywords)
        
        if client_config.custom_intents:
            base_config["custom_intents"] = client_config.custom_intents
        
        base_config["industry"] = industry
        base_config["risk_threshold"] = client_config.risk_threshold or 0.5
        base_config["language_codes"] = client_config.language_codes or []
        base_config["summary_length"] = client_config.summary_length or 100
        base_config["enable_timeline_analysis"] = client_config.enable_timeline_analysis or False
        
        return base_config
    
    def _apply_industry_rules(self, result: Dict, config: Dict, text: Optional[str]) -> Dict:
        """
        Apply industry-specific business rules.
        """
        if not text:
            return result
        
        text_lower = text.lower()
        
        # Check for required phrases
        missing_required = []
        for phrase in config.get("required_phrases", []):
            if phrase.lower() not in text_lower:
                missing_required.append(phrase)
        
        if missing_required:
            warnings = result.get("warnings", [])
            warnings.append(f"Missing required phrases: {', '.join(missing_required)}")
            result["warnings"] = warnings
            
            # Increase risk score for missing required phrases
            if "advanced_analysis" in result:
                result["advanced_analysis"]["risk_score"] = min(100, result["advanced_analysis"]["risk_score"] + 20)
        
        # Check for prohibited phrases
        found_prohibited = []
        for phrase in config.get("prohibited_phrases", []):
            if phrase.lower() in text_lower:
                found_prohibited.append(phrase)
        
        if found_prohibited:
            warnings = result.get("warnings", [])
            warnings.append(f"Prohibited phrases detected: {', '.join(found_prohibited)}")
            result["warnings"] = warnings
            
            # Significantly increase risk score for prohibited phrases
            if "advanced_analysis" in result:
                result["advanced_analysis"]["risk_score"] = min(100, result["advanced_analysis"]["risk_score"] + 40)
        
        # Apply industry-specific risk factors
        if "advanced_analysis" in result:
            risk_score = result["advanced_analysis"]["risk_score"]
            
            for factor, weight in config.get("risk_factors", {}).items():
                if self._check_risk_factor(factor, text_lower):
                    risk_score = min(100, risk_score + int(weight * 100))
            
            result["advanced_analysis"]["risk_score"] = risk_score
        
        return result
    
    def _apply_custom_rules(self, result: Dict, config: Optional[RequestConfig], text: Optional[str]) -> Dict:
        """
        Apply custom business rules from client configuration.
        """
        if not config or not text:
            return result
        
        text_lower = text.lower()
        
        # Check custom compliance keywords
        if config.compliance_keywords:
            found_keywords = [kw for kw in config.compliance_keywords if kw.lower() in text_lower]
            
            if found_keywords:
                # Add compliance flags for custom keywords
                if "advanced_analysis" in result and "compliance_flags" in result["advanced_analysis"]:
                    from app.models.schemas import ComplianceCategory
                    
                    for keyword in found_keywords:
                        flag = {
                            "category": ComplianceCategory.OTHER,
                            "severity": "medium",
                            "description": f"Custom compliance keyword detected: {keyword}",
                            "evidence": keyword,
                            "confidence": 0.7
                        }
                        result["advanced_analysis"]["compliance_flags"].append(flag)
        
        # Apply custom intent filtering
        if config.custom_intents and "primary_intents" in result.get("insights", {}):
            filtered_intents = []
            for intent in result["insights"]["primary_intents"]:
                if intent["name"] in config.custom_intents or intent.get("category") in config.custom_intents:
                    filtered_intents.append(intent)
            
            if filtered_intents:
                result["insights"]["primary_intents"] = filtered_intents
        
        return result
    
    def _apply_sentiment_weights(self, result: Dict, config: Dict) -> Dict:
        """
        Apply industry-specific sentiment weights.
        """
        if "insights" not in result or "overall_sentiment" not in result["insights"]:
            return result
        
        sentiment = result["insights"]["overall_sentiment"]
        sentiment_label = sentiment.get("label", "neutral")
        
        # Get weight for this sentiment
        weight = config.get("sentiment_weights", {}).get(sentiment_label, 1.0)
        
        # Adjust confidence based on weight
        original_confidence = sentiment.get("confidence", 0.5)
        weighted_confidence = min(1.0, original_confidence * weight)
        
        result["insights"]["overall_sentiment"]["confidence"] = weighted_confidence
        
        return result
    
    def _apply_risk_threshold(self, result: Dict, config: Optional[RequestConfig]) -> Dict:
        """
        Apply risk threshold filtering.
        """
        if not config or "advanced_analysis" not in result:
            return result
        
        threshold = config.risk_threshold or 0.5
        current_risk = result["advanced_analysis"]["risk_score"] / 100.0  # Convert to 0-1 scale
        
        if current_risk < threshold:
            # Below threshold - reduce risk indicators
            result["advanced_analysis"]["risk_score"] = int(threshold * 100)
            
            # Remove low-confidence compliance flags
            if "compliance_flags" in result["advanced_analysis"]:
                filtered_flags = [
                    flag for flag in result["advanced_analysis"]["compliance_flags"]
                    if flag.get("confidence", 0) >= threshold
                ]
                result["advanced_analysis"]["compliance_flags"] = filtered_flags
        
        return result
    
    def _check_risk_factor(self, factor: str, text: str) -> bool:
        """
        Check if a specific risk factor is present in the text.
        """
        risk_indicators = {
            "missing_disclosure": ["disclosure", "inform", "notify", "advise"],
            "identity_not_verified": ["verify", "identity", "authenticate", "confirm"],
            "fraud_suspicion": ["fraud", "suspicious", "unusual", "strange"],
            "privacy_violation": ["privacy", "personal", "confidential", "sensitive"],
            "regulatory_breach": ["regulation", "compliance", "breach", "violation"],
            "service_outage": ["outage", "down", "unavailable", "broken"],
            "billing_dispute": ["dispute", "wrong", "incorrect", "overcharge"],
            "contract_violation": ["contract", "agreement", "breach", "violation"],
            "security_breach": ["breach", "hack", "compromise", "unauthorized"],
            "data_leak": ["leak", "expose", "share", "disclose"],
            "sla_breach": ["sla", "service level", "agreement", "deadline"],
            "quality_issue": ["quality", "standard", "poor", "bad"],
            "customer_dissatisfaction": ["unhappy", "dissatisfied", "terrible", "awful"]
        }
        
        indicators = risk_indicators.get(factor, [])
        return any(indicator in text for indicator in indicators)
    
    def validate_config(self, config: RequestConfig) -> List[str]:
        """
        Validate client configuration and return list of issues.
        """
        issues = []
        
        # Validate industry
        if config.industry and config.industry not in self.industry_configs:
            issues.append(f"Unknown industry: {config.industry}")
        
        # Validate risk threshold
        if config.risk_threshold is not None and (config.risk_threshold < 0 or config.risk_threshold > 1):
            issues.append("Risk threshold must be between 0 and 1")
        
        # Validate summary length
        if config.summary_length is not None and (config.summary_length < 50 or config.summary_length > 500):
            issues.append("Summary length must be between 50 and 500 words")
        
        # Validate language codes
        if config.language_codes:
            valid_codes = ["en", "es", "fr", "de", "it", "pt", "hi", "bn", "ta", "te", "zh", "ja", "ko", "ar", "ru"]
            for code in config.language_codes:
                if code not in valid_codes:
                    issues.append(f"Invalid language code: {code}")
        
        return issues
    
    def get_industry_template(self, industry: str) -> Optional[Dict]:
        """
        Get industry configuration template.
        """
        return self.industry_configs.get(industry)
    
    def export_config(self, config: RequestConfig) -> str:
        """
        Export configuration to JSON string.
        """
        return config.json(indent=2)
    
    def import_config(self, config_json: str) -> RequestConfig:
        """
        Import configuration from JSON string.
        """
        try:
            config_dict = json.loads(config_json)
            return RequestConfig(**config_dict)
        except Exception as e:
            logger.error("Failed to import configuration", error=str(e))
            raise ValueError(f"Invalid configuration JSON: {str(e)}")
