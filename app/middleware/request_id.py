import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add unique request IDs for tracing and debugging.
    """
    
    async def dispatch(self, request: Request, call_next):
        # Generate or extract request ID
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        
        # Add to request state
        request.state.request_id = request_id
        
        # Process request
        response = await call_next(request)
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response

def get_request_id(request: Request) -> str:
    """
    Get the request ID from the request state.
    """
    return getattr(request.state, "request_id", str(uuid.uuid4()))
