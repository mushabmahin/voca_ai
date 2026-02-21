#  VOCA AI -- Multilingual Conversation Intelligence Platform

## 📌 Overview

VOCA AI is an enterprise-grade conversation intelligence system that
analyzes multi-speaker conversations (text or audio) to extract:

-   Business domain detection
-   Sentiment & emotion analysis
-   Timeline-based emotion tracking
-   Risk scoring & escalation prediction
-   Compliance & guardrail violations
-   Agent performance insights

------------------------------------------------------------------------

##  Architecture

User Input (Text / Audio) 
          ↓ 
Speech-to-Text (Whisper GPU) 
          ↓ 
Conversation Structuring 
          ↓ 
LLM Analysis (Groq LLaMA 3.1) 
          ↓ 
Guardrail Engine 
          ↓ 
Risk Engine
          ↓ 
Structured JSON Output

------------------------------------------------------------------------

## AI Usage Approach

### 1.Large Language Model (Groq)

Used for: - Domain detection - Multilingual detection - Sentiment &
emotion extraction - Intent detection - Timeline-based emotional
progression

### 2️. Whisper (GPU Accelerated)

Used for: - Audio transcription - Primary language detection

### 3️. Hybrid Guardrail System

Rule-based detection of: - Offensive language - Legal threats - Data
privacy risks - Out-of-scope conversation - Agent misconduct

------------------------------------------------------------------------

## Configuration Mechanism

Environment variables:

GROQ_API_KEY=your_key_here

Optional: HF_HUB_DISABLE_SYMLINKS_WARNING=1

Model configuration in audio_service.py:

WhisperModel("medium", device="cuda", compute_type="float16")

------------------------------------------------------------------------

## 🔌 API Endpoints

### POST /api/analyze/text

Analyzes structured 2-way conversation.

### POST /api/analyze/audio

Accepts audio file and performs speech-to-text + analysis.

------------------------------------------------------------------------

## ⚠ Limitations

-   Manglish/Hinglish detection depends on transliteration accuracy
-   Whisper accuracy depends on audio clarity
-   Risk scoring is heuristic-based
-   No real-time streaming support (batch processing)
-   No persistent storage layer

------------------------------------------------------------------------

## Future Improvements

-   Real-time streaming emotion tracking
-   Agent scoring (0--100)
-   Escalation probability ML model
-   Dashboard UI with emotion graph
-   Multi-tenant domain configuration
-   Vector database for historical analytics
-   Fine-tuned multilingual sentiment model
-   RAG-based compliance policy matching

------------------------------------------------------------------------

## What Makes This Enterprise-Ready

✔ Multilingual\
✔ Multi-speaker\
✔ Audio + Text\
✔ Explainable risk scoring\
✔ Guardrail governance\
✔ Timeline-based analytics\
✔ Structured JSON output

------------------------------------------------------------------------

## Contact

For questions or demo requests, please reach out to the development
team.
