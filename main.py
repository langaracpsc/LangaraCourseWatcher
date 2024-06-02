from datetime import datetime
import time
from typing import TYPE_CHECKING
import schedule
import uvicorn
import requests
import threading
import sys
import gzip

from schedule import every, repeat

import os
from dotenv import load_dotenv
load_dotenv()

from Controller import Controller



DB_LOCATION="database/database.db"
CACHE_DB_LOCATION="database/cache/cache.db"
PREBUILTS_DIRECTORY="database/prebuilts/"
ARCHIVES_DIRECTORY="database/archives/"


if __name__ == "__main__":
    
    
    controller = Controller()

    if not os.path.exists("database/"):
        os.mkdir("database")
        
    if not os.path.exists("database/cache"):
        os.mkdir("database/cache")

    if not os.path.exists(PREBUILTS_DIRECTORY):
        os.mkdir(PREBUILTS_DIRECTORY)

    if not os.path.exists(ARCHIVES_DIRECTORY):
        os.mkdir(ARCHIVES_DIRECTORY)

    if (os.path.exists(DB_LOCATION)):
        print("Database found.")
    else:
        print("Database not found. Building database from scratch.")
        controller.create_db_and_tables()
        controller.buildDatabase()
        
    @repeat(every(60).minutes)
    def hourly():
        controller.updateLatestSemester()
        controller.genIndexesAndPreBuilts()
    
    @repeat(every(24).hours)
    def daily():
        controller.buildDatabase()
            
        
    print("Launching uvicorn.")
    uvicorn.run("api:app", host="0.0.0.0", port=5000)
        