import requests
import requests_cache



def createSession(db_location:str, use_cache=False) -> requests_cache.CachedSession | requests.Session:
    if use_cache:
        return requests_cache.CachedSession(
            # "database/cache",# CACHE_LOCATION, 
            # backend="filesystem",
            db_location, 
            backend="sqlite",
            allowable_methods=("GET", "POST"),
            ignored_parameters=["_wpnonce"]
        )
    else:
        return requests.Session()