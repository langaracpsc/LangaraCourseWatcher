
import time

from sdk.schema.Attribute import AttributeDB
from sdk.schema.CourseSummary import CourseSummaryDB
from sdk.schema.Section import SectionDB
from sdk.schema.ScheduleEntry import ScheduleEntryDB
from sdk.schema.Transfer import Transfer

from sqlmodel import Field, Session, SQLModel, create_engine, select, col

from sdk.scrapers.DownloadLangaraInfo import fetchTermFromWeb
from sdk.parsers.SemesterParser import parseSemesterHTML
from sdk.parsers.CatalogueParser import parseCatalogueHTML
from sdk.parsers.AttributesParser import parseAttributesHTML

class Controller():    
    def __init__(self, db_path="database/database.db", db_type="sqlite") -> None:
        self.transfers = []
        
        connect_args = {"check_same_thread": False}
        self.engine = create_engine(f"{db_type}:///{db_path}", connect_args=connect_args)
    
    # you should probably call this before doing anything
    def create_db_and_tables(self):
        # create db and tables if they don't already exist
        SQLModel.metadata.create_all(self.engine)
    
    
    def incrementTerm(year, term) -> tuple[int, int]:
        if term == 10:
            return (year, 20)
        elif term == 20:
            return (year, 30)
        elif term == 30:
            return (year+1, 10)
    
    
    # Assumes that database is populated.
    def getLatestSemester(db_engine) -> tuple[int, int] | None:
        with Session(db_engine) as session:
            statement = select(SectionDB.year, SectionDB.term).order_by(col(SectionDB.year).desc(), col(SectionDB.term).desc())
            latestSemester = session.exec(statement).first()
        
        return latestSemester
    
    
    # Update the latest semester.
    def updateLatestSemester(self, use_cache=False) -> list[tuple[SectionDB | ScheduleEntryDB | None, SectionDB | ScheduleEntryDB]]:
         
        latestSemester = Controller.getLatestSemester(self.engine)       
        assert latestSemester != None, "Database is empty!"
        
        year = latestSemester[0]
        term = latestSemester[1]
        
        changes = self.updateSemester(year, term, use_cache)
        
        # now = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        # print(f"[{now}] Fetched new data from Langara. {len(changes)} changes found.")
        return changes
    
    

    class SemesterInternal(SQLModel):
        year: int               = Field(description='Year of semester e.g. ```2024```.')
        term: int               = Field(description='Term of semester e.g. ```30```.')
        
        attributes: list[AttributeDB]           = Field(default=[])
        courseSummaries: list[CourseSummaryDB]  = Field(default=[])
        sections: list[SectionDB]               = Field(default=[], description='List of sections in the semester.')
        schedules: list[ScheduleEntryDB]        = Field(default=[])
    
    # Takes approx. 5 minutes to build from cache
    def updateSemester(self, year, term, use_cache=False) -> None | list[tuple[SectionDB | ScheduleEntryDB | None, SectionDB | ScheduleEntryDB]]:
        
        warehouse = Controller.SemesterInternal(year=year, term=term)
        
        termHTML = fetchTermFromWeb(year, term, use_cache=use_cache)
        if termHTML == None:
            return None
        
        sectionsHTML = termHTML[0]
        catalogueHTML = termHTML[1]
        attributesHTML = termHTML[2]
        
        
        # Parse sections and their schedules
        warehouse.sections, warehouse.schedules = parseSemesterHTML(sectionsHTML)
        print(f"{year}{term} : {len(warehouse.sections)} sections found.")
        
        # Parse course summaries from the catalogue
        # ugly atm because parsing is broken for courses before 2012
        warehouse.courseSummaries = parseCatalogueHTML(catalogueHTML, year, term)
        if warehouse.courseSummaries != None:
            print(f"{year}{term} : {len(warehouse.courseSummaries)} unique courses found.")
        else:
            print(f"{year}{term} : Catalogue parsing failed.")
            warehouse.courseSummaries = []
        
        warehouse.attributes = parseAttributesHTML(attributesHTML, year, term)
        print(f"{year}{term} : {len(warehouse.attributes)} courses with attributes found.")
        
        
        # print(f"{year}{term} : Beginning DB update.")

        changes = []
                
        # SQLModel is awesome in some ways and then absolutely unuseable in other ways
        # why is ADD IGNORE EXISTING not implemented ._.
        # TODO: this is horribly slow - it needs a rewrite/optimizations
        with Session(self.engine) as session:
            
            # TODO: get everything before changes to track what is different
            # wondering if the changes function should be pushed to its own service
            # statement = select(Section).where(Section.year == year, Section.term == term).join()
            
            for c in warehouse.sections:
                statement = select(SectionDB).where(SectionDB.year == c.year, SectionDB.term == c.term, SectionDB.crn == c.crn).limit(1)
                results = session.exec(statement)
                result = results.first()
                
                # insert if it doesn't exist
                if result == None:
                    session.add(c)
                    changes.append((None, c))
                    
                # update if it already exists
                else:
                    new_data = c.model_dump()
                    result.sqlmodel_update(new_data)
                    session.add(result)
                
            
            for s in warehouse.schedules:
                
                statement = select(ScheduleEntryDB).where(ScheduleEntryDB.year == s.year, ScheduleEntryDB.term == s.term, ScheduleEntryDB.crn == s.crn, ScheduleEntryDB.type == s.type, ScheduleEntryDB.days == s.days, ScheduleEntryDB.time == s.time).limit(1)
                results = session.exec(statement)
                result = results.first()
                
                # insert if it doesn't exist or update if it already exists
                if result == None:
                    session.add(s)
                    changes.append((None, s))
                else:
                    new_data = s.model_dump()
                    result.sqlmodel_update(new_data)
                    session.add(result)
                    
            for cs in warehouse.courseSummaries:
                statement = select(CourseSummaryDB).where(CourseSummaryDB.year == cs.year, CourseSummaryDB.term == cs.term, CourseSummaryDB.subject == cs.subject, CourseSummaryDB.course_code == cs.course_code).limit(1)
                results = session.exec(statement)
                result = results.first()
                
                # insert if it doesn't exist or update if it already exists
                if result == None:
                    session.add(cs)
                    changes.append((None, cs))
                else:
                    new_data = cs.model_dump()
                    result.sqlmodel_update(new_data)
                    session.add(result)
            
            for a in warehouse.attributes:
                statement = select(AttributeDB).where(AttributeDB.year == a.year, AttributeDB.term == a.term, AttributeDB.subject == a.subject, AttributeDB.course_code == a.course_code).limit(1)
                results = session.exec(statement)
                result = results.first()
                
                # insert if it doesn't exist or update if it already exists
                if result == None:
                    session.add(a)
                    changes.append((None, a))
                else:
                    new_data = a.model_dump()
                    result.sqlmodel_update(new_data)
                    session.add(result)
            
                
                
                
            session.commit()
        
        print(f"{year}{term} : Finished DB update.")
        
        return changes
            
        
    # Build the entire database from scratch.
    # Takes approximately an hour.
    def buildDatabase(self, use_cache=False):
        start = time.time()
        

        # takes approx. 20 minutes live or 8 minutes from cache
        year, term = 1999, 20 # oldest records available on Banner
        while True:
            
            out = self.updateSemester(year, term, use_cache)
            
            if out == None: # this means we've parsed all results
                print(f"{year}{term} : No courses found!")
                break
            
            year, term = Controller.incrementTerm(year, term)
            
            print()
        
        # Download / Save Transfer Information
        # TODO: fix transfer information
        # s = TransferScraper(headless=True)
        # s.downloadAllSubjects(start_at=0)
        # TransferScraper.sendPDFToDatabase(self.db, delete=True)
        
        
        end = time.time()
        # convert time difference until nicely printed output
        # yes, the hours field is unfortunately neccessary
        hours, rem = divmod(end-start, 3600)
        minutes, seconds = divmod(rem, 60)
        total = "{:0>2}:{:0>2}:{:02d}".format(int(hours),int(minutes),int(seconds))
        
        print(f"Database built in {total}!")

        
# c = Controller()
# c.create_db_and_tables()
# c.updateLatestSemester()
# c.buildDatabase(use_cache=True)

# sec = Section(RP=None, seats=1, crn=99999, subject="CPSC", course_code=1050, credits=3, year=2024, term=20)
# # course = Course(RP=None, subject="CPSC", course_code=1050, credits=3, title="THIS IS A TEST, DELETE ME", description=None, hours_lecture=0, hours_lab=0, hours_seminar=0, attr_ar=False)

# with Session(c.engine) as session:
#     session.add(sec)
#     session.commit()