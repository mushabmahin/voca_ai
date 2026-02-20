from pydantic import BaseModel
from typing import List, Optional

class ClientConfig(BaseModel):
    domain: str
    products: List[str]
    policies: List[str]
    risk_triggers: List[str]

class AnalyzeRequest(BaseModel):
    input_type: str  # "text" or "audio"
    conversation: Optional[str] = None
    client_config: ClientConfig

class AnalyzeResponse(BaseModel):
    summary: str
    language: List[str]
    sentiment: str
    intents: List[str]
    topics: List[str]
    compliance_issues: List[str]
    risk_score: int
    call_outcome: str