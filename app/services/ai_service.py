import os
import json
from groq import Groq
from dotenv import load_dotenv
from app.services.compliance_engine import rule_based_compliance_check
from app.services.risk_engine import calculate_risk_assessment

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def clean_json_response(text: str):
    text = text.strip()

    if text.startswith("```"):
        text = text.split("```")[1]

    if text.startswith("json"):
        text = text[4:]

    return text.strip()


async def analyze_conversation(conversation, client_config, detected_language=None):

    conversation_text = "\n".join(
        [f"{msg['speaker'].upper()}: {msg['text']}" for msg in conversation]
    )

    system_message = """
You are an enterprise-grade conversation intelligence engine.

CRITICAL RULES:
- Use provided Business Domain.
- Do NOT re-detect domain.
- All analytical outputs MUST be in English.
- Return STRICT valid JSON only.
"""

    prompt = f"""
Client Context:
- Business Domain: {client_config.domain}
- Products: {client_config.products}
- Policies: {client_config.policies}
- Risk Triggers: {client_config.risk_triggers}

Tasks:
1. Generate summary.
2. Detect languages (if not provided).
3. Provide sentiment, emotion, emotion_intensity.
4. Identify intents and topics.
5. Evaluate agent professionalism.
6. Generate explainable risk_assessment.

Required JSON format:
{{
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

Conversation:
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

        # 🔹 Override language for audio
        if detected_language:
            language_map = {
                "ml": "Malayalam",
                "te": "Telugu",
                "hi": "Hindi",
                "en": "English"
            }
            parsed_output["language"] = [
                language_map.get(detected_language, detected_language)
            ]

        if "compliance_issues" not in parsed_output:
            parsed_output["compliance_issues"] = []

        # 🔹 Guardrail
        rule_violations = rule_based_compliance_check(
            conversation_text,
            client_config.policies
        )

        parsed_output["compliance_issues"].extend(rule_violations)

        # 🔹 Risk boost
        severity_boost = sum(
            20 if v["severity"] == "High"
            else 10 if v["severity"] == "Medium"
            else 5
            for v in rule_violations
        )

        base_score = parsed_output["risk_assessment"].get("score", 0)

        risk_data = calculate_risk_assessment(
            base_score + severity_boost,
            client_config.risk_triggers,
            conversation_text,
            parsed_output.get("emotion_intensity", "Low")
        )

        parsed_output["risk_assessment"] = risk_data

        return parsed_output

    except Exception as e:
        print("Parsing Error:", e)
        print("Raw Output:", raw_output)

        return {
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
            "compliance_issues": [],
            "risk_assessment": {
                "score": 0,
                "level": "Low",
                "factors": []
            },
            "call_outcome": "Unknown"
        }