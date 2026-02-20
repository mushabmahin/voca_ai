# VOCA AI API Examples

This document provides examples of how to use the VOCA AI API for conversation analysis.

## Setup

1. Start the server:
```bash
cd app
python main.py
```

2. The API will be available at `http://localhost:8000`
3. Interactive docs available at `http://localhost:8000/docs`

## Authentication

For development, the server starts with authentication disabled. To enable authentication:

```bash
export REQUIRE_AUTH=true
python main.py
```

Default development API key: `voca_dev_1234567890abcdef`

## API Endpoints

### 1. Analyze Text Conversation

**Endpoint:** `POST /v1/analyze/text`

**Headers:**
```
Content-Type: application/json
Authorization: Bearer voca_dev_1234567890abcdef  (if auth enabled)
```

**Request Body:**
```json
{
  "text": "I'm really frustrated with your service. I've been trying to resolve this issue with my account for weeks and nobody seems to help.",
  "config": {
    "industry": "banking",
    "compliance_keywords": ["account verification", "identity verification"],
    "risk_threshold": 0.6,
    "summary_length": 100,
    "enable_timeline_analysis": false
  }
}
```

**Response:**
```json
{
  "conversation_id": "12345678-1234-1234-1234-123456789012",
  "metadata": {
    "request_id": "req-123456",
    "timestamp": "2024-01-15T10:30:00Z",
    "processing_time_ms": 2500,
    "input_type": "text",
    "file_size_bytes": 150,
    "model_version": "1.0.0",
    "warnings": []
  },
  "insights": {
    "detected_language": ["en"],
    "language_confidence": {"en": 0.95},
    "summary": "Customer expresses frustration about unresolved account issues despite multiple attempts over several weeks, seeking immediate assistance.",
    "overall_sentiment": {
      "label": "negative",
      "confidence": 0.85,
      "emotions": [{"anger": 0.7}, {"frustration": 0.6}]
    },
    "primary_intents": [
      {
        "name": "complaint",
        "confidence": 0.9,
        "category": "customer_service"
      }
    ],
    "key_entities": {
      "person": [{"type": "person", "value": "Customer", "confidence": 0.8}],
      "custom": [{"type": "custom", "value": "account issues", "confidence": 0.7}]
    },
    "advanced_analysis": {
      "risk_score": 65,
      "compliance_flags": [],
      "call_outcome": "escalated",
      "escalation_detected": true,
      "resolution_status": "unresolved"
    }
  }
}
```

### 2. Analyze Audio Conversation

**Endpoint:** `POST /v1/analyze`

**Headers:**
```
Content-Type: multipart/form-data
Authorization: Bearer voca_dev_1234567890abcdef  (if auth enabled)
```

**Form Data:**
```
audio: [audio file]
config: {"industry": "telecom", "risk_threshold": 0.5}
```

**Response:** Same format as text analysis

### 3. Get Supported Formats

**Endpoint:** `GET /v1/analyze/supported-formats`

**Response:**
```json
{
  "audio_formats": [".wav", ".mp3", ".m4a"],
  "max_file_size_mb": 50,
  "max_audio_duration_minutes": 5,
  "text_encoding": ["utf-8", "ascii"],
  "supported_languages": [
    "en", "es", "fr", "de", "it", "pt", "nl", "sv", "da", "no",
    "hi", "bn", "ta", "te", "mr", "gu", "kn", "ml", "pa", "ur",
    "zh", "ja", "ko", "ar", "ru", "tr", "pl", "vi", "th", "id"
  ]
}
```

### 4. Health Check

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "service": "VOCA AI",
  "version": "1.0.0",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 5. Metrics (Authentication Required)

**Endpoint:** `GET /v1/metrics`

**Response:**
```json
{
  "uptime_seconds": 3600,
  "uptime_formatted": "1:00:00",
  "requests": {
    "total": 150,
    "errors": 5,
    "error_rate_percent": 3.33,
    "by_endpoint": {"POST /v1/analyze/text": 100, "POST /v1/analyze": 50}
  },
  "processing": {
    "avg_time_ms": 2500,
    "p50_time_ms": 2000,
    "p95_time_ms": 4000,
    "p99_time_ms": 6000
  }
}
```

## Configuration Options

### Industry Types
- `banking` - Banking and financial services
- `telecom` - Telecommunications
- `fintech` - Financial technology
- `bpo` - Business process outsourcing
- `general` - General customer service

### Configuration Parameters
- `industry`: Industry type for specialized analysis
- `compliance_keywords`: Custom keywords to monitor for compliance
- `custom_intents`: Custom intent categories
- `risk_threshold`: Risk detection threshold (0.0-1.0)
- `language_codes`: Expected languages (ISO 639-1 codes)
- `summary_length`: Target summary length in words
- `enable_timeline_analysis`: Enable timeline-based sentiment analysis

## Error Responses

### 400 Bad Request
```json
{
  "error": "Bad Request",
  "message": "Text transcript is required",
  "request_id": "req-123456",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 401 Unauthorized
```json
{
  "error": "Unauthorized",
  "message": "Invalid API key",
  "request_id": "req-123456",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 429 Rate Limited
```json
{
  "error": "Rate Limit Exceeded",
  "message": "Rate limit exceeded",
  "request_id": "req-123456",
  "timestamp": "2024-01-15T10:30:00Z",
  "details": {"retry_after": 3600}
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal Server Error",
  "message": "An unexpected error occurred",
  "request_id": "req-123456",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Python Client Example

```python
import requests
import json

# API Configuration
BASE_URL = "http://localhost:8000"
API_KEY = "voca_dev_1234567890abcdef"

# Headers
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

# Analyze text
def analyze_text(text, config=None):
    url = f"{BASE_URL}/v1/analyze/text"
    data = {"text": text}
    if config:
        data["config"] = config
    
    response = requests.post(url, headers=headers, json=data)
    return response.json()

# Example usage
conversation = "I'm having trouble with my internet connection. It's been down for 3 days."
config = {
    "industry": "telecom",
    "risk_threshold": 0.5
}

result = analyze_text(conversation, config)
print(json.dumps(result, indent=2))
```

## cURL Example

```bash
# Analyze text
curl -X POST "http://localhost:8000/v1/analyze/text" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer voca_dev_1234567890abcdef" \
  -d '{
    "text": "Customer is frustrated with service quality",
    "config": {
      "industry": "general",
      "risk_threshold": 0.5
    }
  }'

# Upload audio file
curl -X POST "http://localhost:8000/v1/analyze" \
  -H "Authorization: Bearer voca_dev_1234567890abcdef" \
  -F "audio=@conversation.wav" \
  -F 'config={"industry": "banking", "risk_threshold": 0.6}'
```
