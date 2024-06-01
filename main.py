from datetime import datetime
import time
import schedule
import uvicorn
import requests
import threading
import sys
import gzip

# from sdk import Database
# from sdk.Database import Utilities
from discord import send_webhooks

import os
from dotenv import load_dotenv
load_dotenv()

DB_LOCATION="database/LangaraCourseInfo.db"
DB_EXPORT_LOCATION="database/LangaraCourseInfoExport.db"

CACHE_LOCATION="database/cache/cache.db"


if __name__ == "__main__":
    
    print("Launching Langara Course Watcher.")
        
    if (os.path.exists(DB_LOCATION)):
        print("Database found.")
        pass

        
    # LAUNCH API
    print("Launching uvicorn.")
    uvicorn.run("api:app", host="0.0.0.0", port=5000)
        