"""
Authentication layer for the REST API endpoints.

Generates a secure Bearer token on initialization and enforces its
presence and validity on all protected routes.
"""

import os
import secrets
from fastapi import Security, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from focus_mode_app.api.config import API_AUTH_TOKEN_FILE
from focus_mode_app.api.logger import api_logger

security = HTTPBearer()


def get_or_create_token() -> str:
    """
    Retrieve the exact 32-character authentication token from disk, generating
    a new one securely if not found.

    Returns:
        str: The 32-character hex authentication token.
    """
    if API_AUTH_TOKEN_FILE.exists():
        try:
            with open(API_AUTH_TOKEN_FILE, "r") as f:
                token = f.read().strip()
                if token:
                    return token
        except PermissionError:
            api_logger.error(f"Cannot read token file: {API_AUTH_TOKEN_FILE}")

    # Generate a cryptographically secure 16-byte token (32 hex characters)
    new_token = secrets.token_hex(16)

    try:
        API_AUTH_TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        # Touch the file
        with open(API_AUTH_TOKEN_FILE, "w") as f:
            f.write(new_token)

        # Try to restrict permissions to the owner, safely handling OS limitations
        try:
            os.chmod(API_AUTH_TOKEN_FILE, 0o600)
        except OSError:
            pass  # Non-POSIX or filesystem restrictions

        api_logger.info("New API authentication token generated and saved.")
    except Exception as e:
        api_logger.error(f"Failed to generate API auth token file: {e}")

    return new_token


# Cache the exact token globally to avoid constant file I/O per request
_ACTIVE_TOKEN = get_or_create_token()


def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> str:
    """
    FastAPI Dependency to validate the Bearer token associated with the request.

    Uses a constant-time comparison (secrets.compare_digest) to prevent
    timing-based attacks.

    Args:
        credentials (HTTPAuthorizationCredentials): Parsed Authorization header.

    Raises:
        HTTPException: Raises 401 Unauthorized if the token doesn't exactly match.

    Returns:
        str: The provided, validated token value.
    """
    is_valid = secrets.compare_digest(credentials.credentials, _ACTIVE_TOKEN)

    if not is_valid:
        api_logger.warning("Failed authentication attempt: Invalid Token.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return credentials.credentials
