import httpx

DEFAULT_MAX_RETRIES = 2
DEFAULT_TIMEOUT = httpx.Timeout(timeout=60.0, connect=5.0)

# Jittered exponential backoff bounds, in seconds.
INITIAL_RETRY_DELAY = 0.5
MAX_RETRY_DELAY = 8.0
