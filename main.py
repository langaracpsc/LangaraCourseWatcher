import sys
import time

import os
from dotenv import load_dotenv

from schedule import every, repeat, run_pending

import logging

import logging
logger = logging.getLogger("LangaraCourseWatcherScraper") 
logger.setLevel(logging.INFO)

screen_handler = logging.StreamHandler()
formatter = logging.Formatter(fmt='[%(asctime)s] : [%(levelname)-8s] : %(message)s',
                                datefmt='%Y-%m-%d %H:%M:%S')
screen_handler.setFormatter(formatter)
logger.addHandler(screen_handler)


from Controller import Controller
load_dotenv()



DB_LOCATION="database/database.db"
CACHE_DB_LOCATION="database/cache/cache.db"
PREBUILTS_DIRECTORY="database/prebuilts/"
ARCHIVES_DIRECTORY="database/archives/"

   
@repeat(every(60).minutes)
def hourly(use_cache: bool = False):
    c = Controller()
    c.updateLatestSemester(use_cache)
    c.setMetadata("last_updated")


@repeat(every(24).hours)
def daily(use_cache: bool = False):
    c = Controller()
    
    # check for next semester
    c.checkIfNextSemesterExistsAndUpdate()
    
    c.buildDatabase(use_cache)
    c.setMetadata("last_updated")
    
    



if __name__ == "__main__":
    logger.info("Launching Langara Course Watcher")
    
    if not os.path.exists("database/"):
        os.mkdir("database")
        
    if not os.path.exists("database/cache"):
        os.mkdir("database/cache")

    if not os.path.exists(PREBUILTS_DIRECTORY):
        os.mkdir(PREBUILTS_DIRECTORY)

    if not os.path.exists(ARCHIVES_DIRECTORY):
        os.mkdir(ARCHIVES_DIRECTORY)



    if (os.path.exists(DB_LOCATION)):
        logger.info("Database found.")
        controller = Controller()
        controller.create_db_and_tables()
        # controller.checkIfNextSemesterExistsAndUpdate()
        hourly(use_cache=True)
        daily(use_cache=True)
        controller.setMetadata("last_updated")
    else:
        logger.info("Database not found. Building database from scratch.")
        # save results to cache if cache doesn't exist
        controller = Controller()
        controller.create_db_and_tables()
        controller.buildDatabase(use_cache=False)
        controller.setMetadata("last_updated")
    
    logger.info("Finished intialization.")
    
    # hourly()
    # daily()
     
    while True:
        run_pending()
        time.sleep(1)