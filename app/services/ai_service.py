import os
import json
from groq import Groq
from dotenv import load_dotenv
from app.models.schemas import AnalyzeRequest
from app.services.compliance_engine import rule_based_compliance_check
from app.services.risk_engine import calculate_risk_score

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

async def analyze_conversation(request: AnalyzeRequest):

    prompt = f"""
You are an enterprise-grade conversation intelligence engine.

Client Context:
- Domain: {request.client_config.domain}
- Products: {request.client_config.products}
- Policies: {request.client_config.policies}
- Risk Triggers: {request.client_config.risk_triggers}

Analyze the following conversation.

IMPORTANT:
- Regardless of input language, ALL output must be in English.
- Translate any detected information to English.
- Return STRICT JSON only.

Required JSON format:
{{
  "summary": "",
  "language": [],
  "sentiment": "",
  "intents": [],
  "topics": [],
  "compliance_issues": [],
  "risk_score": 0,
  "call_outcome": ""
}}

Conversation:
{request.conversation}
"""

    response = client.chat.completions.create(
    model="llama-3.1-8b-instant",
    messages=[
        {"role": "system", "content": "Return only valid JSON. No explanation text."},
        {"role": "user", "content": prompt}
    ],
    temperature=0.2
)

    raw_output = response.choices[0].message.content.strip()

    try:
        parsed_output = json.loads(raw_output)

        # Safety fallback
        if "compliance_issues" not in parsed_output:
            parsed_output["compliance_issues"] = []

        # 🔹 Rule-based compliance engine
        rule_violations = rule_based_compliance_check(
            request.conversation,
            request.client_config.policies
        )

        parsed_output["compliance_issues"].extend(rule_violations)

        # 🔹 Risk score adjustment
        adjusted_risk = calculate_risk_score(
            parsed_output.get("risk_score", 0),
            request.client_config.risk_triggers,
            request.conversation
        )

        parsed_output["risk_score"] = adjusted_risk

        return parsed_output

    except json.JSONDecodeError:
        return {
            "summary": "Error parsing AI output",
            "language": [],
            "sentiment": "Unknown",
            "intents": [],
            "topics": [],
            "compliance_issues": ["Model returned invalid JSON"],
            "risk_score": 0,
            "call_outcome": "Unknown"
        }