import requests
import requests_cache

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from main import CACHE_DB_LOCATION


def createSession(use_cache=False) -> requests_cache.CachedSession | requests.Session:
    if use_cache:
        return requests_cache.CachedSession(
            # "database/cache",# CACHE_LOCATION, 
            # backend="filesystem",
            CACHE_DB_LOCATION, 
            backend="sqlite",
            allowable_methods=("GET", "POST")
        )
    else:
        return requests.Session()