from pydantic import BaseModel
from typing import List


class ClientConfig(BaseModel):
    domain: str
    products: List[str]
    policies: List[str]
    risk_triggers: List[str]


class AnalyzeRequest(BaseModel):
    text: str
    client_config: ClientConfig


class AnalyzeResponse(BaseModel):
    detected_domain: str
    summary: str
    language: List[str]
    sentiment: str
    emotion: str
    emotion_intensity: str
    intents: List[str]
    topics: List[str]
    agent_analysis: dict
    compliance_issues: List[dict]
    risk_assessment: dict
    call_outcome: str