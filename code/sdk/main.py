# from LangaraCourseInfo import Database, Utilities
# from scrapers.DownloadTransferInfo import TransferScraperManager

# db = Database()
# u = Utilities(db)

import asyncio

from scrapers.BcTransferGuide import TransferScraper

if __name__ == "__main__":
    asyncio.run(TransferScraper.get_all_transfer_information())
    
# print(subjects)

#u.buildDatabaseFromScratch()

#TransferScraper.retrieveAllPDFFromDatabase(db)
#u.rebuildDatabaseFromStored()


#u.rebuildDatabaseFromStored()
#u.buildDatabase(skipTransfer=True)

#TransferScraperManager.fetch_new_data(db=db)
#TransferScraperManager.sendPDFToDatabase(db)
#TransferScraperManager.retrieveAllPDFFromDatabase(db)

#c = db.getSection(2024, 10, 10282)


#for c in c.schedule:
#    print(c)
# u.buildDatabase()

#u.buildDatabase()

#updates = u.updateCurrentSemester()

#u.exportDatabase()

#u.databaseSummary()
