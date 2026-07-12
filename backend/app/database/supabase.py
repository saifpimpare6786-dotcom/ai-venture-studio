from supabase import create_client, Client
from app.core.config import settings

def get_supabase_client() -> Client:
    """
    Creates and returns a Supabase client using the service role key.
    Note: Service role key bypasses Row Level Security (RLS) and is intended
    solely for secure backend operations.
    """
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
