from fastapi import Request,HTTPException
from database import is_ip_whitelisted  # Changed to match function name
from ratelimit import allow  # Fixed: rate_limit -> ratelimit

async def security(request:Request,call_next):
    ip=request.client.host
    if not is_ip_whitelisted(ip):
        raise HTTPException(403,"IP not allowed")

    if not allow(ip):
        raise HTTPException(429,"Rate limit exceeded")

    return await call_next(request)