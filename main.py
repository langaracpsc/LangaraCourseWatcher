from datetime import datetime
import time
import schedule
import uvicorn
import requests
import threading
import sys
import gzip

import os
from dotenv import load_dotenv
load_dotenv()



DB_LOCATION="database/database.db"
CACHE_DB_LOCATION="database/cache/cache.db"
PREBUILTS_DIRECTORY="database/prebuilts/"
ARCHIVES_DIRECTORY="database/archives/"


if __name__ == "__main__":
    print("Launching uvicorn.")
    uvicorn.run("api:app", host="0.0.0.0", port=5000)
        