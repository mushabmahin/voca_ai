import os
import json
from groq import Groq
from dotenv import load_dotenv
from app.models.schemas import AnalyzeRequest
from app.services.compliance_engine import rule_based_compliance_check
from app.services.risk_engine import calculate_risk_assessment

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SUPPORTED_DOMAINS = [
    "Banking",
    "Telecom",
    "Insurance",
    "E-commerce",
    "Healthcare",
    "Travel",
    "General"
]

DOMAIN_RISK_TRIGGERS = {
    "Banking": ["RBI", "fraud", "legal action"],
    "Telecom": ["complaint", "regulatory authority"],
    "Insurance": ["claim dispute", "ombudsman"],
    "Healthcare": ["malpractice", "legal complaint"],
    "E-commerce": ["refund", "consumer court"],
    "Travel": ["cancellation", "compensation"]
}


def clean_json_response(text: str):
    text = text.strip()

    if text.startswith("```"):
        text = text.split("```")[1]

    if text.startswith("json"):
        text = text[4:]

    return text.strip()


async def analyze_conversation(request: AnalyzeRequest):

    # 🔹 Convert structured conversation to readable transcript
    conversation_text = "\n".join(
        [f"{msg.speaker.upper()}: {msg.text}" for msg in request.conversation]
    )

    system_message = """
You are an enterprise conversation intelligence engine.

CRITICAL RULES:
- All analytical outputs MUST be in English.
- Only the 'language' field may contain the original language.
- If input is not English, internally translate before analysis.
- Return ONLY valid JSON.
"""

    prompt = f"""
IMPORTANT INSTRUCTIONS:

1. Detect the business domain.
   Possible domains: {SUPPORTED_DOMAINS}

2. Detect ALL languages used in the conversation.
   - If multiple languages are used, return all of them.
   - The "language" field must be a list of all detected languages.
   - Example: ["Hindi", "English"]
   - Even if only a few words from another language are present,
     include that language in the list.
   - If English words appear within another language (e.g., Manglish or Hinglish),
  include BOTH languages.
   - Example:
      "Ente account block ayi without reason"
       → ["Malayalam", "English"]
      Detect ALL languages used in the conversation.
    - If Malayalam words written in Latin script are present 
      (e.g., "ente", "cheyyanam", "koduthu", "ayi"),
      include "Malayalam" in the language list.

Do NOT ignore Malayalam if it appears in transliterated form.

3. Provide:
   - Detailed summary
   - Sentiment (Positive/Neutral/Negative)
   - Emotion (Angry, Frustrated, Concerned, Calm, etc.)
   - Emotion_intensity (Low/Medium/High)
   - Primary customer intent
   - Key topics

4. Analyze the agent behavior:
   - Professionalism
   - Resolution effectiveness

5. Provide conversation outcome.

6. Generate risk_assessment with:
   - score (0–100)
   - level (Low/Medium/High)
   - factors (list of reasons)

Required JSON format:
{{
  "detected_domain": "",
  "summary": "",
  "language": [],
  "sentiment": "",
  "emotion": "",
  "emotion_intensity": "",
  "intents": [],
  "topics": [],
  "agent_analysis": {{
    "professionalism": "",
    "resolution_effectiveness": ""
  }},
  "compliance_issues": [],
  "risk_assessment": {{
    "score": 0,
    "level": "",
    "factors": []
  }},
  "call_outcome": ""
}}

Conversation Transcript:
{conversation_text}
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1,
        max_tokens=800
    )

    raw_output = response.choices[0].message.content.strip()

    try:
        cleaned_output = clean_json_response(raw_output)
        parsed_output = json.loads(cleaned_output)

        # 🔹 Ensure compliance_issues exists
        if "compliance_issues" not in parsed_output or not isinstance(parsed_output["compliance_issues"], list):
            parsed_output["compliance_issues"] = []

        detected_domain = parsed_output.get("detected_domain", "General")

        # 🔹 Get domain-specific triggers
        triggers = DOMAIN_RISK_TRIGGERS.get(detected_domain, [])

        # 🔹 Run structured guardrail engine
        rule_violations = rule_based_compliance_check(
            conversation_text,
            []
        )

        parsed_output["compliance_issues"].extend(rule_violations)

        # 🔹 Severity-based risk multiplier
        severity_boost = 0
        for violation in rule_violations:
            if violation["severity"] == "High":
                severity_boost += 20
            elif violation["severity"] == "Medium":
                severity_boost += 10
            elif violation["severity"] == "Low":
                severity_boost += 5

        # 🔹 Base AI risk score
        base_score = parsed_output["risk_assessment"].get("score", 0)

        # 🔹 Final explainable risk assessment
        risk_data = calculate_risk_assessment(
            base_score + severity_boost,
            triggers,
            conversation_text,
            parsed_output.get("emotion_intensity", "Low")
        )

        parsed_output["risk_assessment"] = risk_data

        # 🔹 Optional: Guardrail summary
        if rule_violations:
            parsed_output["guardrail_summary"] = {
                "total_violations": len(rule_violations),
                "highest_severity": max(
                    [v["severity"] for v in rule_violations],
                    key=lambda x: {"High": 3, "Medium": 2, "Low": 1}.get(x, 0)
                )
            }

        return parsed_output

    except Exception as e:
        print("AI Parsing Error:", e)
        print("Raw Model Output:", raw_output)

        return {
            "detected_domain": "Unknown",
            "summary": "Error parsing AI output",
            "language": [],
            "sentiment": "Unknown",
            "emotion": "Unknown",
            "emotion_intensity": "Low",
            "intents": [],
            "topics": [],
            "agent_analysis": {
                "professionalism": "Unknown",
                "resolution_effectiveness": "Unknown"
            },
            "compliance_issues": [
                {
                    "type": "System Error",
                    "severity": "High",
                    "message": "Model returned invalid JSON"
                }
            ],
            "risk_assessment": {
                "score": 0,
                "level": "Low",
                "factors": []
            },
            "call_outcome": "Unknown"
        }