from typing import Optional
from supabase import create_client, Client
from app.core.config import settings

_supabase_client: Optional[Client] = None


def get_supabase_client() -> Client:
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY,
        )
    return _supabase_client


async def upload_file(bucket: str, path: str, content: bytes, content_type: str) -> str:
    client = get_supabase_client()
    client.storage.from_(bucket).upload(
        path=path,
        file=content,
        file_options={"content-type": content_type, "upsert": "true"},
    )
    result = client.storage.from_(bucket).get_public_url(path)
    return result


async def get_signed_url(bucket: str, path: str, expires_in: int = 3600) -> str:
    client = get_supabase_client()
    result = client.storage.from_(bucket).create_signed_url(path, expires_in)
    return result.get("signedURL") or result.get("signedUrl", "")


async def delete_file(bucket: str, path: str) -> None:
    client = get_supabase_client()
    client.storage.from_(bucket).remove([path])
