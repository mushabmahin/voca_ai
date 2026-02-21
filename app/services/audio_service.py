from faster_whisper import WhisperModel
import tempfile
import os

# Use GPU if available
model = WhisperModel(
    "medium",
    device="cuda",        # change to "cpu" if no GPU
    compute_type="float16"
)

async def transcribe_audio(file):

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
        temp_audio.write(await file.read())
        temp_path = temp_audio.name

    segments, info = model.transcribe(
        temp_path,
        beam_size=5,
        temperature=0.0
    )

    transcription = " ".join([segment.text for segment in segments])

    os.remove(temp_path)

    return transcription.strip(), info.language