import re

FOUL_WORDS = [
    "idiot", "stupid", "damn", "hell", "bloody", "bastard"
]

THREAT_WORDS = [
    "sue", "legal action", "court", "complaint",
    "police", "lawsuit", "fraud"
]

SENSITIVE_TOPICS = [
    "politics", "religion", "terrorism", "violence"
]

OUT_OF_SCOPE_TOPICS = [
    "cricket", "movie", "celebrity", "gaming", "football"
]

PII_PATTERNS = [
    r"\b\d{12}\b",   # Aadhaar-like
    r"\b\d{16}\b",   # Card number-like
    r"\b\d{10}\b"    # Phone number-like
]


def rule_based_compliance_check(conversation_text: str, policies=None):

    violations = []
    text = conversation_text.lower()

    # 🔹 1. Offensive Language Detection
    for word in FOUL_WORDS:
        if word in text:
            violations.append({
                "type": "Offensive Language",
                "severity": "Medium",
                "message": f"Offensive word detected: '{word}'"
            })

    # 🔹 2. Legal / Escalation Threats
    for word in THREAT_WORDS:
        if word in text:
            violations.append({
                "type": "Escalation Threat",
                "severity": "High",
                "message": f"Legal or escalation term detected: '{word}'"
            })

    # 🔹 3. Sensitive Topic Detection
    for topic in SENSITIVE_TOPICS:
        if topic in text:
            violations.append({
                "type": "Sensitive Topic",
                "severity": "Medium",
                "message": f"Sensitive topic detected: '{topic}'"
            })

    # 🔹 4. Out-of-Scope Discussion
    for topic in OUT_OF_SCOPE_TOPICS:
        if topic in text:
            violations.append({
                "type": "Out of Scope",
                "severity": "Low",
                "message": f"Conversation drifting from business scope: '{topic}'"
            })

    # 🔹 5. PII Exposure Detection
    for pattern in PII_PATTERNS:
        if re.search(pattern, conversation_text):
            violations.append({
                "type": "Data Privacy Risk",
                "severity": "High",
                "message": "Possible personal data exposure detected"
            })

    # 🔹 6. Agent Misconduct Example
    if "agent:" in text and "i don't care" in text:
        violations.append({
            "type": "Agent Misconduct",
            "severity": "High",
            "message": "Agent displayed unprofessional behavior"
        })

    return violations