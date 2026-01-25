import time
from collections import defaultdict
from config import RATE_LIMIT,RATE_WINDOW

bucket=defaultdict(list)

def allow(key):
    now=time.time()\
    bucket[key]=[t for t in bucket[key] if now-t<RATE_WINDOW]
    if len(bucket[key])>=RATE_LIMIT:
        return False
    bucket[key].append(now)
    return True
