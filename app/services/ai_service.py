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

async def analyze_conversation(request: AnalyzeRequest):

    prompt = f"""
You are an enterprise-grade conversation intelligence engine.

IMPORTANT INSTRUCTIONS (MANDATORY):

1. Detect the business domain of the conversation.
   Possible domains: {SUPPORTED_DOMAINS}

2. Detect the original language and return it in the "language" field.

3. If the conversation is NOT in English:
   - First internally translate the conversation into English.
   - Then generate the summary and all analysis based on the English translation.

4. All output fields MUST be written in English.
   The ONLY field allowed to contain non-English text is the "language" field.

5. If any field is not in English, regenerate it in English before returning the final JSON.

6. Provide detailed emotion and emotion_intensity.

Return STRICT valid JSON only. No explanation.

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
  "compliance_issues": [],
  "risk_assessment": {{
    "score": 0,
    "level": "",
    "factors": []
  }},
  "call_outcome": ""
}}

Conversation:
{request.conversation}
"""

    messages = [{"role": "user", "content": prompt}]

    response = client.chat.completions.create(
    model="llama-3.1-8b-instant",
    messages=messages,
    temperature=0.1,
    max_tokens=600
)

    raw_output = response.choices[0].message.content.strip()

    try:
        parsed_output = json.loads(raw_output)

        # Safety fallback
        if "compliance_issues" not in parsed_output:
            parsed_output["compliance_issues"] = []

        detected_domain = parsed_output.get("detected_domain", "General")

        # 🔹 Apply internal domain triggers
        triggers = DOMAIN_RISK_TRIGGERS.get(detected_domain, [])

        # 🔹 Rule-based compliance engine (optional simple rule)
        rule_violations = rule_based_compliance_check(
            request.conversation,
            []  # no external policies now
        )
        parsed_output["compliance_issues"].extend(rule_violations)

        # 🔹 Calculate risk assessment (new format)
        base_score = parsed_output["risk_assessment"]["score"]

        risk_data = calculate_risk_assessment(
            base_score,
            triggers,
            request.conversation,
            parsed_output.get("emotion_intensity", "Low")
        )

        parsed_output["risk_assessment"] = risk_data

        return parsed_output

    except Exception as e:
        print("ERROR:", e)
        return {
            "detected_domain": "Unknown",
            "summary": "Error parsing AI output",
            "language": [],
            "sentiment": "Unknown",
            "emotion": "Unknown",
            "emotion_intensity": "Low",
            "intents": [],
            "topics": [],
            "compliance_issues": ["Model returned invalid JSON"],
            "risk_assessment": {
                "score": 0,
                "level": "Low",
                "factors": []
            },
            "call_outcome": "Unknown"
        }