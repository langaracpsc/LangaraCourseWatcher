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
    
# Refresh course data from Langara sources
# If changes are found, notify sources
def refreshSemester(u, discord_url:str = None) -> None:
    
    #u.databaseSummary()
    changes = u.updateCurrentSemester()
    
    u.exportDatabase(DB_EXPORT_LOCATION)
    
    # prezip export
    with open(DB_EXPORT_LOCATION, 'rb') as f_in:
        with gzip.open(DB_EXPORT_LOCATION + ".gz", 'wb') as f_out:
            f_out.writelines(f_in)
    
    
    if discord_url == None:
        print("No discord webhook found.")
        
    else:
        send_webhooks(discord_url, changes)
        
    now = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{now}] Fetched new data from Langara. {len(changes)} changes found.")

if __name__ == "__main__":
    print("Launching Langara Course Watcher.")
    
        
    if (os.path.exists(DB_LOCATION)):
        print("Database found.")
        pass

    # If no database is in the docker volume, then we should fetch a backup from github
    # We could also build it locally from scratch but that takes over an hour.
    else:
        print("No database found. Downloading from Github...")
        release_url = "https://api.github.com/repos/Highfire1/LangaraCourseInfo/releases/latest"
        response = requests.get(release_url)
        data = response.json()
        assets = data['assets']
        
        asset_url = assets[0]['browser_download_url']
        
        response = requests.get(asset_url)
        if response.status_code == 200:
            with open(DB_LOCATION, 'wb') as file:
                file.write(response.content)
            print(f"Database downloaded to {DB_LOCATION}")
        else:
            print(f"Failed to download the database. Status code: {response.status_code}")
            sys.exit()
        

    # Launch web server
    def start_uvicorn():
        print("Launching uvicorn.")
        uvicorn.run("api:app", host="0.0.0.0", port=5000)
        

    def start_refreshing():
        # Launch 30 minute updates
        webhook_url = os.getenv("DISCORD_WEBHOOK_URL")

        db = Database(DB_LOCATION)
        u = Utilities(db)

        # takes 10 minutes
        #u.rebuildDatabaseFromStored()

        refreshSemester(u, webhook_url)
        schedule.every(30).minutes.do(refreshSemester, u, webhook_url)

        while True:
            schedule.run_pending()
            time.sleep(1)
            
    x = threading.Thread(target=start_refreshing, daemon=True)
    x.start()
    
    start_uvicorn()