"""
Cache Manager
Simple file-based caching system
"""
import json
import os
import time
import hashlib
from typing import Any, Optional, Callable


class CacheManager:
    """Simple file-based cache manager"""
    
    def __init__(self, cache_dir: str = ".cache", ttl: int = 2592000):
        """
        Initialize cache manager
        
        Args:
            cache_dir: Directory to store cache files
            ttl: Time to live in seconds (default: 30 days)
        """
        self.cache_dir = cache_dir
        self.ttl = ttl
        os.makedirs(cache_dir, exist_ok=True)
    
    def _get_cache_path(self, key: str) -> str:
        """Get cache file path for a key"""
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{key_hash}.json")
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
        
        Returns:
            Cached value or None if not found/expired
        """
        cache_path = self._get_cache_path(key)
        
        if not os.path.exists(cache_path):
            return None
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # Check if expired
            if time.time() - cache_data['timestamp'] > self.ttl:
                os.remove(cache_path)
                return None
            
            return cache_data['value']
        except Exception:
            return None
    
    def set(self, key: str, value: Any):
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
        """
        cache_path = self._get_cache_path(key)
        cache_data = {
            'timestamp': time.time(),
            'value': value
        }
        
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f)
        except Exception:
            pass
    
    def get_or_fetch(self, key: str, fetch_func: Callable) -> Any:
        """
        Get from cache or fetch and cache
        
        Args:
            key: Cache key
            fetch_func: Function to fetch value if not cached
        
        Returns:
            Cached or fetched value
        """
        cached = self.get(key)
        if cached is not None:
            return cached
        
        value = fetch_func()
        self.set(key, value)
        return value
