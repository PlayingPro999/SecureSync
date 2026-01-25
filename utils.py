import time
from collections import defaultdict
from config import RATE_LIMIT, RATE_WINDOW

# Simple in-memory rate limiter
# ip -> [timestamps]
_requests = defaultdict(list)

def rate_limited(ip):
    """
    Check if IP has exceeded rate limit.
    Returns True if rate limited, False if allowed.
    """
    now = time.time()
    window_start = now - RATE_WINDOW

    # Remove timestamps outside the current window
    _requests[ip] = [t for t in _requests[ip] if t > window_start]

    # Check if rate limit exceeded
    if len(_requests[ip]) >= RATE_LIMIT:
        return True

    # Add current request timestamp
    _requests[ip].append(now)
    return False

def cleanup_old_entries():
    """
    Periodically clean up old IPs from memory.
    Call this from a background task.
    """
    now = time.time()
    window_start = now - RATE_WINDOW
    
    # Remove IPs with no recent requests
    empty_ips = []
    for ip, timestamps in _requests.items():
        _requests[ip] = [t for t in timestamps if t > window_start]
        if not _requests[ip]:
            empty_ips.append(ip)
    
    for ip in empty_ips:
        del _requests[ip]
