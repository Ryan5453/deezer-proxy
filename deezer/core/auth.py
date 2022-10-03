import secrets

from fastapi import Security
from fastapi.exceptions import HTTPException
from fastapi.security.api_key import APIKeyHeader

from deezer.core.config import auth_key

api_key_header_auth = APIKeyHeader(
    name="Authorization",
    description="Mandatory Authorization, required for all endpoints",
    auto_error=False,
)


async def get_api_key(api_key_header: str = Security(api_key_header_auth)):
    if not auth_key:
        return  # Let's hope the user knows what they're doing

    if not api_key_header:
        raise HTTPException(
            status_code=401, detail="You are missing the Authorization header."
        )

    correct_api_key = secrets.compare_digest(api_key_header, auth_key)
    if correct_api_key is False:
        raise HTTPException(
            status_code=403,
            detail="The API key in the 'Authorization' header is invalid.",
        )
