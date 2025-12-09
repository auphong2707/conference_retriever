"""
Rate Limiter
Token bucket rate limiter for API and web requests
"""
import time


class RateLimiter:
    """Token bucket rate limiter"""
    
    def __init__(self, requests_per_second: float = 1.0):
        """
        Initialize rate limiter
        
        Args:
            requests_per_second: Maximum requests per second
        """
        self.rate = requests_per_second
        self.allowance = requests_per_second
        self.last_check = time.time()
    
    def wait_if_needed(self):
        """Wait if rate limit would be exceeded"""
        current = time.time()
        time_passed = current - self.last_check
        self.last_check = current
        self.allowance += time_passed * self.rate
        
        if self.allowance > self.rate:
            self.allowance = self.rate
        
        if self.allowance < 1.0:
            sleep_time = (1.0 - self.allowance) / self.rate
            time.sleep(sleep_time)
            self.allowance = 0.0
        else:
            self.allowance -= 1.0
