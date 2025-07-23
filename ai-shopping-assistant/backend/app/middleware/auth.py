from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from typing import Optional, Dict, Any
import time

from app.config import settings, logger

# HTTP Bearer token scheme for JWT authentication
security = HTTPBearer(auto_error=False)

class JWTValidationError(Exception):
    """Custom exception for JWT validation errors"""
    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)

class JWTValidator:
    """
    JWT token validation middleware for Auth0 authentication
    """
    
    def __init__(self):
        self.domain = settings.auth0_domain
        self.audience = settings.auth0_api_audience
        self.algorithms = settings.auth0_algorithms
        self.issuer = settings.auth0_issuer
    
    async def validate_token(self, credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Dict[str, Any]:
        """
        Validates the JWT token from the Authorization header
        
        Args:
            credentials: The HTTP Authorization credentials
            
        Returns:
            dict: The decoded JWT payload if valid
            
        Raises:
            HTTPException: If the token is invalid or missing
        """
        if credentials is None:
            raise HTTPException(
                status_code=401,
                detail="Missing authentication token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        token = credentials.credentials
        
        try:
            # Get the JWKS URL from Auth0 domain
            jwks_url = f"https://{self.domain}/.well-known/jwks.json"
            
            # Decode and validate the token
            payload = jwt.decode(
                token,
                jwks_url,
                algorithms=self.algorithms,
                audience=self.audience,
                issuer=self.issuer,
                options={"verify_signature": True, "verify_aud": True, "verify_exp": True}
            )
            
            # Check if token is expired
            if "exp" in payload and payload["exp"] < time.time():
                raise JWTValidationError("Token has expired")
            
            return payload
            
        except JWTError as e:
            logger.error(f"JWT validation error: {str(e)}")
            raise HTTPException(
                status_code=401,
                detail=f"Invalid authentication token: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"}
            )
        except Exception as e:
            logger.error(f"Unexpected error during JWT validation: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Internal server error during authentication",
                headers={"WWW-Authenticate": "Bearer"}
            )

# Create a singleton instance of the JWT validator
jwt_validator = JWTValidator()

# Dependency for protected endpoints
async def get_current_user(token: Dict[str, Any] = Depends(jwt_validator.validate_token)) -> Dict[str, Any]:
    """
    Gets the current authenticated user from the JWT token
    
    Args:
        token: The decoded JWT token
        
    Returns:
        dict: The user information from the token
    """
    # Extract user information from the token
    user_info = {
        "sub": token.get("sub"),
        "email": token.get("email"),
        "name": token.get("name"),
        "picture": token.get("picture")
    }
    
    return user_info

# Optional dependency for endpoints that can be accessed by both authenticated and guest users
async def get_optional_user(request: Request) -> Optional[Dict[str, Any]]:
    """
    Gets the current user if authenticated, or None for guest users
    
    Args:
        request: The FastAPI request object
        
    Returns:
        dict or None: The user information or None for guest users
    """
    auth_header = request.headers.get("Authorization")
    
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    
    token = auth_header.replace("Bearer ", "")
    
    try:
        # Get the JWKS URL from Auth0 domain
        jwks_url = f"https://{settings.auth0_domain}/.well-known/jwks.json"
        
        # Decode and validate the token
        payload = jwt.decode(
            token,
            jwks_url,
            algorithms=settings.auth0_algorithms,
            audience=settings.auth0_api_audience,
            issuer=settings.auth0_issuer,
            options={"verify_signature": True, "verify_aud": True, "verify_exp": True}
        )
        
        # Extract user information from the token
        user_info = {
            "sub": payload.get("sub"),
            "email": payload.get("email"),
            "name": payload.get("name"),
            "picture": payload.get("picture")
        }
        
        return user_info
        
    except Exception as e:
        logger.warning(f"Optional authentication failed: {str(e)}")
        return None


async def get_current_user_id(user: Dict[str, Any] = Depends(get_current_user)) -> str:
    """
    Gets the current user ID from the authenticated user
    
    Args:
        user: The authenticated user information
        
    Returns:
        str: The user ID (sub claim from JWT)
        
    Raises:
        HTTPException: If the user ID is not found in the token
    """
    if not user or "sub" not in user:
        raise HTTPException(
            status_code=401,
            detail="User ID not found in authentication token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return user["sub"]