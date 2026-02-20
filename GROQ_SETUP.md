# Groq API Setup for VOCA AI

Your VOCA AI project now supports Groq API as an alternative to OpenAI! Here's how to set it up:

## 🚀 Quick Setup with Groq

### 1. Get Your Groq API Key
1. Go to [Groq Console](https://console.groq.com/)
2. Sign up or log in
3. Navigate to API Keys section
4. Create a new API key
5. Copy your API key

### 2. Configure Environment
Create a `.env` file in the project root:

```bash
# Copy the example file
cp .env.example .env

# Edit the .env file
# Set your Groq API key
GROQ_API_KEY=gsk_your_groq_api_key_here

# Optional: Leave OpenAI key empty or remove it
# OPENAI_API_KEY=

# Other settings
PORT=8000
ENVIRONMENT=development
REQUIRE_AUTH=false
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Start the Server
```bash
cd app
python main.py
```

The system will automatically detect and use Groq API!

## 🎯 What Groq Provides

**Benefits of Groq:**
- **Faster Response Times**: Groq's inference engine is optimized for speed
- **Cost Effective**: Generally more affordable than OpenAI
- **High Performance**: Excellent for text generation tasks
- **Easy Migration**: Drop-in replacement for OpenAI

**Model Used:**
- Default: `mixtral-8x7b-32768` (can be changed in `.env`)
- You can also use: `llama2-70b-4096`, `gemma-7b-it`

## 📋 Test Your Setup

### Test with Text Analysis
```bash
curl -X POST "http://localhost:8000/v1/analyze/text" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "I am very frustrated with your service quality and nobody is helping me",
    "config": {
      "industry": "general",
      "risk_threshold": 0.5
    }
  }'
```

### Check Which AI Provider is Being Used
```bash
curl http://localhost:8000/health
```

The logs will show:
```
INFO - Using Groq as AI provider
INFO - Groq client initialized model=mixtral-8x7b-32768
```

## 🔧 Configuration Options

### Available Groq Models
```bash
# In your .env file
GROQ_MODEL=mixtral-8x7b-32768        # Default - Great balance
GROQ_MODEL=llama2-70b-4096          # Larger model
GROQ_MODEL=gemma-7b-it              # Smaller, faster
```

### Fallback to OpenAI
If you have both API keys set:
```bash
GROQ_API_KEY=gsk_your_groq_key
OPENAI_API_KEY=sk_your_openai_key
```

The system will prefer Groq if available, but can fall back to OpenAI.

## 🚨 Troubleshooting

### "No AI provider API key found"
- Make sure `GROQ_API_KEY` is set in your `.env` file
- Check that the API key is valid and active

### "Groq library not installed"
```bash
pip install groq
```

### Rate Limit Issues
- Groq has generous rate limits for development
- For production, consider upgrading your Groq plan

### Model Not Available
- Check Groq console for available models
- Update `GROQ_MODEL` in your `.env` file

## 🎊 You're Ready!

Your VOCA AI now uses Groq for:
- ✅ Conversation summarization
- ✅ Sentiment and emotion analysis  
- ✅ Intent and topic extraction
- ✅ Compliance and risk detection
- ✅ All AI-powered features

The API works exactly the same - just faster and more cost-effective with Groq!

## 📚 Next Steps

1. Test with sample conversations from `examples/sample_conversations.txt`
2. Try different industries (banking, telecom, fintech, bpo)
3. Check the interactive docs at `http://localhost:8000/docs`
4. Monitor performance at `http://localhost:8000/v1/metrics`

Enjoy your Groq-powered VOCA AI! 🚀
