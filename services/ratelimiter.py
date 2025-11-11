# services/ratelimiter.py
from threading import Semaphore

class RateLimiter:
    """Controls concurrent requests to prevent API rate limits."""
    def __init__(self, max_concurrent: int = 5):
        self.semaphore = Semaphore(max_concurrent)

    def acquire(self):
        self.semaphore.acquire()

    def release(self):
        self.semaphore.release()
