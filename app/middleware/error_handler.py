import structlog
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.models.schemas import ErrorResponse
import traceback
import uuid

logger = structlog.get_logger()

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Global error handling middleware for consistent error responses.
    """
    
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
            
        except HTTPException as http_exc:
            # HTTP exceptions are already handled properly
            logger.warning(
                "HTTP exception occurred",
                status_code=http_exc.status_code,
                detail=http_exc.detail,
                path=request.url.path
            )
            
            return JSONResponse(
                status_code=http_exc.status_code,
                content=ErrorResponse(
                    error=self._get_error_type(http_exc.status_code),
                    message=http_exc.detail,
                    request_id=getattr(request.state, "request_id", None)
                ).dict()
            )
            
        except Exception as exc:
            # Handle unexpected exceptions
            error_id = str(uuid.uuid4())
            
            logger.error(
                "Unhandled exception occurred",
                error_id=error_id,
                error=str(exc),
                traceback=traceback.format_exc(),
                path=request.url.path,
                method=request.method,
                request_id=getattr(request.state, "request_id", None)
            )
            
            # Don't expose internal details in production
            is_development = os.getenv("ENVIRONMENT", "production") == "development"
            
            error_response = ErrorResponse(
                error="Internal server error",
                message="An unexpected error occurred" if not is_development else str(exc),
                request_id=getattr(request.state, "request_id", None)
            )
            
            if is_development:
                error_response.details = {
                    "error_id": error_id,
                    "traceback": traceback.format_exc()
                }
            
            return JSONResponse(
                status_code=500,
                content=error_response.dict()
            )
    
    def _get_error_type(self, status_code: int) -> str:
        """
        Get error type from HTTP status code.
        """
        error_types = {
            400: "Bad Request",
            401: "Unauthorized",
            403: "Forbidden",
            404: "Not Found",
            405: "Method Not Allowed",
            413: "Payload Too Large",
            422: "Unprocessable Entity",
            429: "Too Many Requests",
            500: "Internal Server Error",
            502: "Bad Gateway",
            503: "Service Unavailable",
            504: "Gateway Timeout"
        }
        
        return error_types.get(status_code, "Unknown Error")

class ValidationError(Exception):
    """
    Custom exception for validation errors.
    """
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details
        super().__init__(message)

class ProcessingError(Exception):
    """
    Custom exception for processing errors.
    """
    def __init__(self, message: str, component: str = None, details: dict = None):
        self.message = message
        self.component = component
        self.details = details
        super().__init__(message)

class ConfigurationError(Exception):
    """
    Custom exception for configuration errors.
    """
    def __init__(self, message: str, config_key: str = None):
        self.message = message
        self.config_key = config_key
        super().__init__(message)

class AuthenticationError(Exception):
    """
    Custom exception for authentication errors.
    """
    def __init__(self, message: str = "Authentication failed"):
        self.message = message
        super().__init__(message)

class RateLimitError(Exception):
    """
    Custom exception for rate limiting errors.
    """
    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = None):
        self.message = message
        self.retry_after = retry_after
        super().__init__(message)

async def validation_exception_handler(request: Request, exc: ValidationError):
    """
    Handle validation exceptions.
    """
    logger.warning(
        "Validation error occurred",
        error=exc.message,
        details=exc.details,
        path=request.url.path,
        request_id=getattr(request.state, "request_id", None)
    )
    
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(
            error="Validation Error",
            message=exc.message,
            request_id=getattr(request.state, "request_id", None),
            details=exc.details
        ).dict()
    )

async def processing_exception_handler(request: Request, exc: ProcessingError):
    """
    Handle processing exceptions.
    """
    logger.error(
        "Processing error occurred",
        component=exc.component,
        error=exc.message,
        details=exc.details,
        path=request.url.path,
        request_id=getattr(request.state, "request_id", None)
    )
    
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Processing Error",
            message=exc.message,
            request_id=getattr(request.state, "request_id", None),
            details=exc.details
        ).dict()
    )

async def configuration_exception_handler(request: Request, exc: ConfigurationError):
    """
    Handle configuration exceptions.
    """
    logger.error(
        "Configuration error occurred",
        config_key=exc.config_key,
        error=exc.message,
        path=request.url.path,
        request_id=getattr(request.state, "request_id", None)
    )
    
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Configuration Error",
            message=exc.message,
            request_id=getattr(request.state, "request_id", None),
            details={"config_key": exc.config_key} if exc.config_key else None
        ).dict()
    )

async def authentication_exception_handler(request: Request, exc: AuthenticationError):
    """
    Handle authentication exceptions.
    """
    logger.warning(
        "Authentication error occurred",
        error=exc.message,
        path=request.url.path,
        request_id=getattr(request.state, "request_id", None)
    )
    
    return JSONResponse(
        status_code=401,
        content=ErrorResponse(
            error="Authentication Error",
            message=exc.message,
            request_id=getattr(request.state, "request_id", None)
        ).dict()
    )

async def rate_limit_exception_handler(request: Request, exc: RateLimitError):
    """
    Handle rate limit exceptions.
    """
    logger.warning(
        "Rate limit exceeded",
        error=exc.message,
        retry_after=exc.retry_after,
        path=request.url.path,
        request_id=getattr(request.state, "request_id", None)
    )
    
    headers = {}
    if exc.retry_after:
        headers["Retry-After"] = str(exc.retry_after)
    
    return JSONResponse(
        status_code=429,
        content=ErrorResponse(
            error="Rate Limit Exceeded",
            message=exc.message,
            request_id=getattr(request.state, "request_id", None),
            details={"retry_after": exc.retry_after} if exc.retry_after else None
        ).dict(),
        headers=headers
    )
