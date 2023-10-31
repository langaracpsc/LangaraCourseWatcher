import schedule
import uvicorn
import requests

from LangaraCourseInfo import Database, Utilities
from discord import send_webhook

import os
from dotenv import load_dotenv
load_dotenv()

DB_LOCATION="database/LangaraCourseInfo.db"
DB_EXPORT_LOCATION="database/LangaraCourseInfoExport.db"


# Refresh course data from Langara sources
# If changes are found, notify sources
def frequent_task(u:Utilities, discord_url:str = None) -> None:
    
    u.databaseSummary()
    changes = u.updateCurrentSemester()
    
    u.exportDatabase(DB_EXPORT_LOCATION)
    
    
    if discord_url == None:
        print("No discord webhook found.")
        return
    
    for c in changes:
        send_webhook(discord_url, c[0], c[1])


if __name__ == "__main__":
    
    if (os.path.exists(DB_LOCATION)):
        print("Database found.")
        pass
    
    # If no database is in the docker volume, then we should fetch a backup form github
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
        
    
    db = Database(DB_LOCATION)
    u = Utilities(db)

    # takes 10 minutes
    #u.rebuildDatabaseFromStored()

    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")

    frequent_task(u, webhook_url)
    schedule.every(30).minutes.do(frequent_task, u, webhook_url)

    print("Launching uvicorn.")
    
    uvicorn.run("api:app", host="0.0.0.0", port=5000)