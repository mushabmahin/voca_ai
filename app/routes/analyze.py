from fastapi import APIRouter, Form, UploadFile, File, HTTPException
from app.services.audio_service import transcribe_audio
from app.services.ai_service import analyze_conversation
from app.models.schemas import AnalyzeRequest

router = APIRouter()

@router.post("/analyze")
async def analyze(
    input_type: str = Form(...),
    conversation: str = Form(None),
    audio_file: UploadFile = File(None)
):

    if input_type == "audio":
        if not audio_file:
            raise HTTPException(status_code=400, detail="Audio file is required")
        conversation_text = await transcribe_audio(audio_file)

    elif input_type == "text":
        if not conversation:
            raise HTTPException(status_code=400, detail="Conversation text is required")
        conversation_text = conversation

    else:
        raise HTTPException(status_code=400, detail="Invalid input_type")

    request_obj = AnalyzeRequest(
        input_type=input_type,
        conversation=conversation_text
    )

    result = await analyze_conversation(request_obj)
    return result