import structlog
from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
import os
import hashlib
import time
from typing import Optional

logger = structlog.get_logger()

# In-memory storage for API keys (in production, use a database)
API_KEYS = {
    # Default development key
    "voca_dev_1234567890abcdef": {
        "name": "Development Key",
        "created_at": "2024-01-01T00:00:00Z",
        "usage_count": 0,
        "rate_limit": 1000,  # requests per hour
        "last_reset": time.time()
    }
}

class APIKeyAuth(BaseHTTPMiddleware):
    """
    Middleware for API key authentication and rate limiting.
    """
    
    async def dispatch(self, request: Request, call_next):
        # Skip authentication for health check and docs
        if request.url.path in ["/", "/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        # Get API key from header
        api_key = self._extract_api_key(request)
        
        if not api_key:
            logger.warning("Missing API key", path=request.url.path)
            raise HTTPException(
                status_code=401,
                detail="API key required",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Validate API key
        key_info = self._validate_api_key(api_key)
        
        if not key_info:
            logger.warning("Invalid API key", key_hash=hashlib.sha256(api_key.encode()).hexdigest()[:8])
            raise HTTPException(
                status_code=401,
                detail="Invalid API key"
            )
        
        # Check rate limit
        if not self._check_rate_limit(key_info):
            logger.warning("Rate limit exceeded", key_name=key_info["name"])
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded"
            )
        
        # Add key info to request state
        request.state.api_key_info = key_info
        
        response = await call_next(request)
        
        # Update usage count
        key_info["usage_count"] += 1
        
        # Add API usage headers
        response.headers["X-API-Usage-Count"] = str(key_info["usage_count"])
        response.headers["X-API-Rate-Limit"] = str(key_info["rate_limit"])
        
        return response
    
    def _extract_api_key(self, request: Request) -> Optional[str]:
        """
        Extract API key from various sources.
        """
        # Try Authorization header (Bearer token)
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header[7:]
        
        # Try X-API-Key header
        api_key_header = request.headers.get("X-API-Key")
        if api_key_header:
            return api_key_header
        
        # Try query parameter (less secure, for testing)
        api_key_query = request.query_params.get("api_key")
        if api_key_query:
            return api_key_query
        
        return None
    
    def _validate_api_key(self, api_key: str) -> Optional[dict]:
        """
        Validate API key and return key info.
        """
        return API_KEYS.get(api_key)
    
    def _check_rate_limit(self, key_info: dict) -> bool:
        """
        Check if the API key has exceeded its rate limit.
        """
        current_time = time.time()
        
        # Reset counter if hour has passed
        if current_time - key_info["last_reset"] > 3600:  # 1 hour
            key_info["usage_count"] = 0
            key_info["last_reset"] = current_time
        
        return key_info["usage_count"] < key_info["rate_limit"]

# HTTPBearer for FastAPI dependency injection
security = HTTPBearer(auto_error=False)

async def get_api_key_info(credentials: Optional[HTTPAuthorizationCredentials] = security) -> Optional[dict]:
    """
    FastAPI dependency to get API key information.
    """
    if not credentials:
        return None
    
    api_key = credentials.credentials
    return API_KEYS.get(api_key)

async def require_api_key(credentials: HTTPAuthorizationCredentials = security) -> dict:
    """
    FastAPI dependency that requires a valid API key.
    """
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="API key required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    api_key = credentials.credentials
    key_info = API_KEYS.get(api_key)
    
    if not key_info:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    
    return key_info

def generate_api_key(name: str, rate_limit: int = 1000) -> str:
    """
    Generate a new API key.
    """
    import secrets
    
    api_key = f"voca_{secrets.token_hex(16)}"
    
    API_KEYS[api_key] = {
        "name": name,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "usage_count": 0,
        "rate_limit": rate_limit,
        "last_reset": time.time()
    }
    
    return api_key

def revoke_api_key(api_key: str) -> bool:
    """
    Revoke an API key.
    """
    if api_key in API_KEYS:
        del API_KEYS[api_key]
        return True
    return False

def list_api_keys() -> list:
    """
    List all API keys (without revealing the actual keys).
    """
    safe_keys = []
    for key, info in API_KEYS.items():
        safe_keys.append({
            "key_id": key[:8] + "...",
            "name": info["name"],
            "created_at": info["created_at"],
            "usage_count": info["usage_count"],
            "rate_limit": info["rate_limit"],
            "is_active": True
        })
    return safe_keys
