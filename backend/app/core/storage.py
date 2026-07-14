import httpx
import structlog
from app.core.config import settings

logger = structlog.get_logger()

# Default Supabase Storage Bucket name for assets
BUCKET_NAME = "products"


def get_public_url(path: str) -> str:
    """Get public CDN URL for an asset. 
    
    If Supabase is configured, returns the Supabase Storage CDN path.
    Otherwise, returns the path unchanged (relative URL for local development).
    """
    if not path:
        return path

    # If it is already an absolute HTTP URL, return it
    if path.startswith(("http://", "https://")):
        return path

    if settings.SUPABASE_URL and settings.SUPABASE_KEY:
        clean_path = path.lstrip("/")
        return f"{settings.SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/{clean_path}"

    return path


async def get_signed_url(path: str, expires_in: int = 3600) -> str:
    """Generate a signed URL for private assets dynamically from Supabase API."""
    if not path:
        return path

    # If it is already an absolute HTTP URL, return it
    if path.startswith(("http://", "https://")):
        return path

    if settings.SUPABASE_URL and settings.SUPABASE_KEY:
        clean_path = path.lstrip("/")
        url = f"{settings.SUPABASE_URL}/storage/v1/object/sign/{BUCKET_NAME}/{clean_path}"
        headers = {
            "Authorization": f"Bearer {settings.SUPABASE_KEY}",
            "Content-Type": "application/json"
        }
        payload = {"expiresIn": expires_in}
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, json=payload, headers=headers, timeout=5.0)
                if resp.status_code == 200:
                    data = resp.json()
                    signed_path = data.get("signedURL") or data.get("signedUrl")
                    if signed_path:
                        if signed_path.startswith("http"):
                            return signed_path
                        return f"{settings.SUPABASE_URL}{signed_path}"
        except Exception as e:
            logger.error("Failed to generate Supabase signed URL", error=str(e), path=path)

    return path
