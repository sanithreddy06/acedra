from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings

# The key is the connection's client address. Behind the bundled Nginx, the API server is started with
# trusted proxy headers, so this is the real visitor address rather than the proxy's.
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[settings.RATE_LIMIT_DEFAULT],
    storage_uri=settings.RATE_LIMIT_STORAGE_URI,
    enabled=settings.ENVIRONMENT != "test",
)
