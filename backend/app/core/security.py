from fastapi import Header, HTTPException, status
from app.database.supabase import get_supabase_client

def get_current_user(authorization: str = Header(...)):
    """
    FastAPI dependency to extract and verify the JWT bearer token from the authorization header.
    Calls Supabase Auth to confirm the session validity.
    Returns the authenticated user details.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header must start with 'Bearer '"
        )
    
    token = authorization.split(" ")[1]
    supabase = get_supabase_client()
    try:
        user_response = supabase.auth.get_user(token)
        if not user_response or not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid session token or expired user session."
            )
        return user_response.user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Session authentication failed: {str(e)}"
        )
