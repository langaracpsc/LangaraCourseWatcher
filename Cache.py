import time
import hashlib
from typing import Any, Dict, Tuple, Callable
from functools import wraps
from fastapi import Response
from requests_cache import Optional

class SQLModelCache:
    def __init__(self, global_ttl: int = 60):
        self.cache_store: Dict[str, Tuple[Any, int]] = {}
        self.global_ttl = global_ttl
        self.oldest_cache_time = float('inf')

    def _hash_query(self, query: str, params: Tuple) -> str:
        """Creates a unique hash for a query and its parameters."""
        hasher = hashlib.sha256()
        hasher.update(query.encode())
        for param in params:
            hasher.update(str(param).encode())
        return hasher.hexdigest()

    def set(self, query: str, params: Tuple, data: Any, ttl: int = None) -> None:
        """Caches the data for a specific query with a TTL."""
        expiry = time.time() + (ttl or self.global_ttl)
        cache_key = self._hash_query(query, params)
        self.cache_store[cache_key] = (data, expiry)
        
        # Update the oldest_cache_time based on new entry
        if expiry < self.oldest_cache_time:
            self.oldest_cache_time = expiry

        self._purge_expired()

    def get(self, query: str, params: Tuple) -> Any:
        """Fetches cached data if it exists and hasn't expired; otherwise, returns None."""
        self._purge_expired()  # Purge if needed before fetching
        cache_key = self._hash_query(query, params)
        cached = self.cache_store.get(cache_key)
        
        if cached:
            data, expiry = cached
            if time.time() < expiry:
                return data
            # Expire entry if TTL is reached
            del self.cache_store[cache_key]
        
        return None

    def _purge_expired(self) -> None:
        """Removes expired cache entries based on the oldest_cache_time."""
        current_time = time.time()
        if current_time > self.oldest_cache_time:
            self.cache_store = {
                key: (data, expiry)
                for key, (data, expiry) in self.cache_store.items()
                if expiry > current_time
            }
            # Reset the oldest_cache_time
            self.oldest_cache_time = min(
                (expiry for _, expiry in self.cache_store.values()), 
                default=float('inf')
            )

    def clear(self) -> None:
        """Clears the entire cache."""
        self.cache_store.clear()
        self.oldest_cache_time = float('inf')

    def set_global_ttl(self, ttl: int) -> None:
        """Sets a global TTL for all cache entries."""
        self.global_ttl = ttl

    def cache_decorator(self, ttl: int = None):
        """Decorator for caching function results based on query parameters."""
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                
                # Add support for FastAPI response header
                response: Optional[Response] = copy_kwargs.pop(response_param.name, None)
                
                query_str = kwargs.get("query_str", "")
                params = kwargs.get("params", ())

                cached_result = self.get(query_str, params)
                if cached_result is not None:
                    if response:
                        response.headers["X-FastAPI-Cache"] = "HIT"
                    return cached_result

                if response:
                    response.headers["X-FastAPI-Cache"] = "MISS"
                
                # Execute the function and cache the result
                result = await func(*args, **kwargs)
                self.set(query_str, params, result, ttl)
                return result
            return wrapper
        return decorator
