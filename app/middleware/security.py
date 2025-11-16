from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.config import settings
import re
import html

limiter = Limiter(key_func=get_remote_address)


def sanitize_input(text: str) -> str:
    """Sanitize input to prevent XSS and SQL injection"""
    if not text:
        return ""
    # HTML escape
    text = html.escape(text)
    # Remove potential SQL injection patterns
    text = re.sub(r"([';]|(--)|(/\*)|(\*/)|(xp_)|(sp_))", "", text, flags=re.IGNORECASE)
    return text.strip()


def validate_sql_safe(text: str) -> bool:
    """Validate that text doesn't contain SQL injection patterns"""
    dangerous_patterns = [
        r"(\bor\b|\band\b)\s+\d+\s*=\s*\d+",
        r"union\s+select",
        r"drop\s+table",
        r"delete\s+from",
        r"insert\s+into",
        r"update\s+.*\s+set",
        r"exec\s*\(",
        r"execute\s*\(",
    ]
    text_lower = text.lower()
    for pattern in dangerous_patterns:
        if re.search(pattern, text_lower):
            return False
    return True


def setup_security_middleware(app: FastAPI):
    """Setup security middleware"""
    
    # Rate limiting
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    @app.middleware("http")
    async def security_middleware(request: Request, call_next):
        """Security middleware for input sanitization"""
        
        # Skip security checks for health check and static files
        if request.url.path in ["/health", "/"]:
            return await call_next(request)
        
        # Sanitize query parameters
        if request.query_params:
            sanitized_params = {}
            for key, value in request.query_params.items():
                if not validate_sql_safe(value):
                    return JSONResponse(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        content={
                            "error": True,
                            "message": "Invalid input detected",
                            "status_code": 400
                        }
                    )
                sanitized_params[key] = sanitize_input(value)
            # Note: FastAPI doesn't allow modifying query_params directly
            # This is a validation step
        
        response = await call_next(request)
        return response

