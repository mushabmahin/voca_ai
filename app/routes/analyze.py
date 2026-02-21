from fastapi import APIRouter, UploadFile, File, HTTPException, Body
from app.services.audio_service import transcribe_audio
from app.services.ai_service import analyze_conversation
from app.models.schemas import AnalyzeRequest

router = APIRouter()

# 🔹 TEXT (2-Way Structured Conversation)
@router.post("/analyze/text")
async def analyze_text(request: AnalyzeRequest = Body(...)):

    if request.input_type != "text":
        raise HTTPException(status_code=400, detail="Invalid input_type for text endpoint")

    result = await analyze_conversation(request)
    return result


# 🔹 AUDIO (Single file input)
@router.post("/analyze/audio")
async def analyze_audio(audio_file: UploadFile = File(...)):

    conversation_text = await transcribe_audio(audio_file)

    request_obj = AnalyzeRequest(
        input_type="text",
        conversation=[
            {"speaker": "customer", "text": conversation_text}
        ]
    )

    result = await analyze_conversation(request_obj)
    return result