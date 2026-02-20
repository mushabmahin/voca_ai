from faster_whisper import WhisperModel
import tempfile
import os

model = WhisperModel(
    "large-v2",
    device="cpu",
    compute_type="int8"
)

async def transcribe_audio(file):

    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
        temp_audio.write(await file.read())
        temp_path = temp_audio.name

    # Better transcription settings
    segments, info = model.transcribe(
        temp_path,
        beam_size=5,
        best_of=5,
        temperature=0.0,
        vad_filter=True,   # Voice activity detection
        language=None      # Auto detect
    )

    transcription = " ".join([segment.text for segment in segments])

    print("Detected language:", info.language)
    print("Language probability:", info.language_probability)
    print("Transcription:", transcription)

    os.remove(temp_path)

    return transcription.strip()