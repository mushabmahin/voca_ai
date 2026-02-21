from fastapi import APIRouter, UploadFile, File, Body
from app.services.audio_service import transcribe_audio
from app.services.ai_service import analyze_conversation
from app.models.schemas import AnalyzeRequest, ClientConfig
import json

router = APIRouter()


def parse_text_to_structured(text: str):
    lines = text.split("\n")
    structured = []

    for line in lines:
        if line.lower().startswith("agent:"):
            structured.append({
                "speaker": "agent",
                "text": line.replace("Agent:", "").strip()
            })
        elif line.lower().startswith("customer:"):
            structured.append({
                "speaker": "customer",
                "text": line.replace("Customer:", "").strip()
            })
        else:
            structured.append({
                "speaker": "customer",
                "text": line.strip()
            })

    return structured


# 🔹 TEXT ENDPOINT
@router.post("/analyze/text")
async def analyze_text(request: AnalyzeRequest = Body(...)):

    structured_conversation = parse_text_to_structured(request.text)

    result = await analyze_conversation(
        structured_conversation,
        request.client_config,
        detected_language=None  # LLM handles text detection
    )

    return result


# 🔹 AUDIO ENDPOINT
@router.post("/analyze/audio")
async def analyze_audio(
    audio_file: UploadFile = File(...),
    client_config: str = Body(...)
):

    # Convert JSON string → dict → ClientConfig
    config_dict = json.loads(client_config)
    config_obj = ClientConfig(**config_dict)

    transcription, detected_language = await transcribe_audio(audio_file)

    structured_conversation = [
        {"speaker": "customer", "text": transcription}
    ]

    result = await analyze_conversation(
        structured_conversation,
        config_obj,
        detected_language=detected_language
    )

    return result