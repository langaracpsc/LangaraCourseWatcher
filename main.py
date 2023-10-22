import schedule
import uvicorn

from LangaraCourseInfo import Database, Utilities

from discord import send_webhook
import os
from dotenv import load_dotenv
load_dotenv()

db = Database()
u = Utilities(db)



def task():
    
    u.databaseSummary()
    
    changes = u.updateCurrentSemester()
    
    u.exportDatabase("LangaraCourseInfoExport.db")
    
    
    url = os.getenv("DISCORD_WEBHOOK_URL")
    if url == None:
        print("No discord webhook found.")
        return
    
    for c in changes:
        send_webhook(url, c[0], c[1])



task()
schedule.every( 30 ).minutes.do(task)


# webapi
# uvicorn api.Api:app --host localhost --port 5000 --reload
if __name__ == "__main__":
    print("Launching uvicorn.")
    
    uvicorn.run("api:app", host="0.0.0.0", port=5000)