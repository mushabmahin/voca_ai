from fastapi import APIRouter, UploadFile, File, Form
from app.models.schemas import AnalyzeRequest, AnalyzeResponse
from app.services.ai_service import analyze_conversation
from app.services.audio_service import transcribe_audio
import json

router = APIRouter()

@router.post("/analyze")
async def analyze(
    input_type: str = Form(...),
    client_config: str = Form(...),
    conversation: str = Form(None),
    audio_file: UploadFile = File(None)
):
    try:
        config_dict = json.loads(client_config)
    except Exception:
        return {"error": "Invalid client_config JSON format"}

    if input_type == "audio":
        transcription = await transcribe_audio(audio_file)
        conversation_text = transcription
    else:
        conversation_text = conversation

    request_obj = AnalyzeRequest(
        input_type=input_type,
        conversation=conversation_text,
        client_config=config_dict
    )

    result = await analyze_conversation(request_obj)
    return result