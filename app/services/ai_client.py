import structlog
import os
from typing import Optional, Dict, Any
import httpx
from enum import Enum

logger = structlog.get_logger()

class AIProvider(Enum):
    OPENAI = "openai"
    GROQ = "groq"

class AIClient:
    """
    Unified AI client that supports both OpenAI and Groq APIs.
    Automatically detects available API keys and uses the preferred provider.
    """
    
    def __init__(self):
        self.provider = self._detect_provider()
        self.client = None
        self.model = None
        self._initialize_client()
    
    def _detect_provider(self) -> AIProvider:
        """
        Detect which AI provider to use based on available API keys.
        Groq is preferred if available, otherwise OpenAI.
        """
        # Try to load .env from parent directory
        import os
        from pathlib import Path
        
        # Get the project root directory
        current_dir = Path(__file__).parent.parent.parent
        env_file = current_dir / ".env"
        
        if env_file.exists():
            from dotenv import load_dotenv
            load_dotenv(env_file)
        
        groq_key = os.getenv("GROQ_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")
        
        if groq_key:
            logger.info("Using Groq as AI provider")
            return AIProvider.GROQ
        elif openai_key:
            logger.info("Using OpenAI as AI provider")
            return AIProvider.OPENAI
        else:
            raise ValueError("No AI provider API key found. Please set GROQ_API_KEY or OPENAI_API_KEY")
    
    def _initialize_client(self):
        """
        Initialize the appropriate AI client based on provider.
        """
        if self.provider == AIProvider.GROQ:
            self._initialize_groq_client()
        elif self.provider == AIProvider.OPENAI:
            self._initialize_openai_client()
    
    def _initialize_groq_client(self):
        """
        Initialize Groq client.
        """
        try:
            from groq import Groq
            self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
            self.model = os.getenv("GROQ_MODEL", "mixtral-8x7b-32768")
            logger.info("Groq client initialized", model=self.model)
        except ImportError:
            logger.error("Groq library not installed. Install with: pip install groq")
            raise
        except Exception as e:
            logger.error("Failed to initialize Groq client", error=str(e))
            raise
    
    def _initialize_openai_client(self):
        """
        Initialize OpenAI client.
        """
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            self.model = "gpt-3.5-turbo"
            logger.info("OpenAI client initialized", model=self.model)
        except ImportError:
            logger.error("OpenAI library not installed. Install with: pip install openai")
            raise
        except Exception as e:
            logger.error("Failed to initialize OpenAI client", error=str(e))
            raise
    
    async def chat_completion(
        self,
        messages: list,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> str:
        """
        Create a chat completion using the configured AI provider.
        """
        try:
            if self.provider == AIProvider.GROQ:
                return await self._groq_chat_completion(
                    messages, temperature, max_tokens, **kwargs
                )
            elif self.provider == AIProvider.OPENAI:
                return await self._openai_chat_completion(
                    messages, temperature, max_tokens, **kwargs
                )
        except Exception as e:
            logger.error("Chat completion failed", provider=self.provider.value, error=str(e))
            raise
    
    async def _groq_chat_completion(
        self,
        messages: list,
        temperature: float,
        max_tokens: int,
        **kwargs
    ) -> str:
        """
        Groq chat completion.
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error("Groq chat completion failed", error=str(e))
            raise
    
    async def _openai_chat_completion(
        self,
        messages: list,
        temperature: float,
        max_tokens: int,
        **kwargs
    ) -> str:
        """
        OpenAI chat completion.
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error("OpenAI chat completion failed", error=str(e))
            raise
    
    def get_provider_info(self) -> Dict[str, Any]:
        """
        Get information about the current AI provider.
        """
        return {
            "provider": self.provider.value,
            "model": self.model,
            "client_initialized": self.client is not None
        }

# Global AI client instance
ai_client = AIClient()

def get_ai_client() -> AIClient:
    """
    Get the global AI client instance.
    """
    return ai_client
