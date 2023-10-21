import schedule
import uvicorn

from LangaraCourseInfo import Database, Utilities
from LangaraCourseInfo import Course

from discord import send_webhook

db = Database("LangaraCourseInfoExport.db")
u = Utilities(db)



def task():
    
    u.databaseSummary()
    
    changes = u.updateCurrentSemester()
    
    u.exportDatabase("LangaraCourseInfoExport2.db")
    
    for c in changes:
        send_webhook(c[0], c[1])



task()
schedule.every( 30 ).minutes.do(task)


# webapi
# uvicorn api.Api:app --host localhost --port 5000 --reload
if __name__ == "__main__":
    print("Launching uvicorn.")
    
    uvicorn.run("api:app", host="0.0.0.0", port=5000)