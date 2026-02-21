from pydantic import BaseModel
from typing import List, Optional

class ClientConfig(BaseModel):
    domain: str
    products: List[str]
    policies: List[str]
    risk_triggers: List[str]

class Message(BaseModel):
    speaker: str  # "agent" or "customer"
    text: str


class AnalyzeRequest(BaseModel):
    input_type: str
    conversation: List[Message]

class AnalyzeResponse(BaseModel):
    summary: str
    language: List[str]
    sentiment: str
    intents: List[str]
    topics: List[str]
    compliance_issues: List[str]
    risk_score: int
    call_outcome: str