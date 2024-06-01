
import json
import time

from sqlalchemy import union

from main import PREBUILTS_DIRECTORY
from sdk.schema.Attribute import AttributeDB
from sdk.schema.CourseSummary import CourseSummaryDB
from sdk.schema.Section import SectionAPI, SectionDB
from sdk.schema.ScheduleEntry import ScheduleEntryDB
from sdk.schema.Transfer import Transfer, TransferDB

from sqlmodel import Field, Session, SQLModel, create_engine, select, col
from sqlalchemy.orm import selectinload 
from pydantic.json import pydantic_encoder

from sdk.schema_built.Course import CourseBase, CourseAPIBuild, CourseDB
from sdk.scrapers.DownloadLangaraInfo import fetchTermFromWeb
from sdk.parsers.SemesterParser import parseSemesterHTML
from sdk.parsers.CatalogueParser import parseCatalogueHTML
from sdk.parsers.AttributesParser import parseAttributesHTML
from sdk.scrapers.DownloadTransferInfo import getTransferInformation

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
        self._generateCourseIndexes()
        
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
    
    def updateSemester(self, year, term, use_cache=False) -> bool | None:
        
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
        # ugly conditional because parsing is broken for courses before 2012
        warehouse.courseSummaries = parseCatalogueHTML(catalogueHTML, year, term)
        if warehouse.courseSummaries != None:
            print(f"{year}{term} : {len(warehouse.courseSummaries)} unique courses found.")
        else:
            print(f"{year}{term} : Catalogue parsing failed.")
            warehouse.courseSummaries = []
        
        warehouse.attributes = parseAttributesHTML(attributesHTML, year, term)
        print(f"{year}{term} : {len(warehouse.attributes)} unique courses with attributes found.")
        
        
        # print(f"{year}{term} : Beginning DB update.")
                
        # SQLModel is awesome in some ways and then absolutely unuseable in other ways
        # why is ADD IGNORE EXISTING not implemented ._.
        # TODO: this is horribly slow - it needs a rewrite/optimizations
        with Session(self.engine) as session:
            
            # TODO: move changes watcher to its own service
            
            for c in warehouse.sections:
                result = session.get(SectionDB, c.id)
                
                # insert if it doesn't exist or update if it does exist
                if result == None:
                    session.add(c)
                else:
                    new_data = c.model_dump()
                    result.sqlmodel_update(new_data)
                    session.add(result)
                
            
            for s in warehouse.schedules:
                result = session.get(ScheduleEntryDB, s.id)
                
                # insert if it doesn't exist or update if it already exists
                if result == None:
                    session.add(s)
                else:
                    new_data = s.model_dump()
                    result.sqlmodel_update(new_data)
                    session.add(result)
                    
            for cs in warehouse.courseSummaries:
                result = session.get(CourseSummaryDB, cs.id)
                
                # insert if it doesn't exist or update if it already exists
                if result == None:
                    session.add(cs)
                else:
                    new_data = cs.model_dump()
                    result.sqlmodel_update(new_data)
                    session.add(result)
            
            for a in warehouse.attributes:
                result = session.get(AttributeDB, a.id)
                
                # insert if it doesn't exist or update if it already exists
                if result == None:
                    session.add(a)
                else:
                    new_data = a.model_dump()
                    result.sqlmodel_update(new_data)
                    session.add(result)

            session.commit()
                    
        
        print(f"{year}{term} : Finished DB update.")
        return True
        
    
    def timeDeltaString(time1:float, time2:float) -> str:
        hours, rem = divmod(time2-time1, 3600)
        minutes, seconds = divmod(rem, 60)
        return "{:0>2}:{:0>2}:{:02d}".format(int(hours),int(minutes),int(seconds))
        
            
        
    # Build the entire database from scratch.
    # Takes approximately an hour. (?) NOT TRUE
    def buildDatabase(self, use_cache=False):
        print("Building database...\n")
        start = time.time()        

        # Download / Save Langara Tnformation
        # Takes ? time from live and 11 minutes from cache
        year, term = 1999, 20 # oldest records available on Banner
        while True:
            
            out = self.updateSemester(year, term, use_cache)
            print()
            
            if out == None: # this means we've parsed all results
                print(f"{year}{term} : No courses found!")
                break
            
            year, term = Controller.incrementTerm(year, term)
        
        timepoint1 = time.time()
        print(f"Langara information downloaded and parsed in {Controller.timeDeltaString(start, timepoint1)}")
        print()
        
        # Download / Save Transfer Information
        # Takes ? time from live and 22 seconds from cache.
        transfers = getTransferInformation(use_cache=True)
        
        with Session(self.engine) as session:
            for i, t in enumerate(transfers):
                if i % 5000==0:
                    print(f"Storing transfer agreements... ({i}/{len(transfers)})")
                
                statement = select(TransferDB).where(TransferDB.id == t.id).limit(1)
                results = session.exec(statement)
                result = results.first()
                
                # insert if it doesn't exist or update if it already exists
                if result == None:
                    session.add(t)
                else:
                    new_data = t.model_dump()
                    result.sqlmodel_update(new_data)
                    session.add(result)
            
            session.commit()
        
        timepoint2 = time.time()
        print(f"Transfer information downloaded and parsed in {Controller.timeDeltaString(timepoint1, timepoint2)}")    
        print()
        
        # Takes approximately 1.5 minutes
        print("Generating aggregated course data.")
        self.genIndexesAndPreBuilts()
        
        timepoint3 = time.time()
        print(f"Database indexes built in {Controller.timeDeltaString(timepoint2, timepoint3)}") 
        
        
        print(f"Database built in {Controller.timeDeltaString(start, timepoint3)}!")
    
    
    def genIndexesAndPreBuilts(self) -> None:
        # self._generateCourseIndexes()
        self._generatePreBuilds()
        
    def _generatePreBuilds(self) -> None:    
        
        out = []

        # get all courses for the given semester
        with Session(self.engine) as session:
            statement = select(SectionDB.subject, SectionDB.course_code).distinct()
            results = session.exec(statement)
            courses = results.all()
            
        for c in courses:
            out.append(self.buildCourse(c[0], c[1], return_offerings=True))
            
        with open(PREBUILTS_DIRECTORY + "allInfo.json", "w+") as fi:
            fi.write(json.dumps(out, default=pydantic_encoder))
    
    
    def _generateCourseIndexes(self) -> None:
        # get list of courses
        with Session(self.engine) as session:
            statement = select(CourseSummaryDB.subject, CourseSummaryDB.course_code).distinct()
            statement2 = select(SectionDB.subject, SectionDB.course_code).distinct()

            results = session.exec(union(statement, statement2))
            courses = results.all() 
            
            i = 0
            
            for subject, course_code in courses:
                if i % 250 == 0:
                    print(f"Generating indexes... ({i}/{len(courses)+1})")
                i+=1
                    
                c = CourseDB(
                    id=f"CRS-{subject}-{course_code}",
                    subject=subject, 
                    course_code=course_code
                )
                                
                statement = select(AttributeDB).where(
                    AttributeDB.subject == subject,
                    AttributeDB.course_code == course_code
                ).order_by(col(AttributeDB.year).desc(), col(AttributeDB.term).desc()).limit(1) 
                result = session.exec(statement).first()
                if result:
                    c.latest_attribute_id = result.id
                
                
                statement = select(CourseSummaryDB).where(CourseSummaryDB.subject == subject, CourseSummaryDB.course_code == course_code).order_by(col(CourseSummaryDB.year).desc(), col(CourseSummaryDB.term).desc()).limit(1)
                results = session.exec(statement)
                result = results.first()
                if result:
                    c.latest_course_summary_id = result.id
                    
                    
                statement = select(SectionDB).where(
                    SectionDB.subject == subject, 
                    SectionDB.course_code == course_code
                    ).order_by(col(SectionDB.year).desc(), col(SectionDB.term).desc()
                    ).limit(1)
                    
                results = session.exec(statement)
                result = results.first()
                # a course can have info out without a section being public yet 
                if result:
                    c.latest_section_id = result.id
                
                # save
                # print(c.id)
                statement = select(CourseDB).where(CourseDB.id == c.id).limit(1)
                results = session.exec(statement)
                result = results.first()
                # print(result)
                
                # insert if it doesn't exist or update if it already exists
                if result == None:
                    session.add(c)
                else:
                    new_data = c.model_dump()
                    result.sqlmodel_update(new_data)
                    session.add(result)
                    
                    
                session.commit()
        
        
    def buildCourse(self, subject, course_code, return_offerings=True) -> CourseAPIBuild | None:
                
        with Session(self.engine) as session:
            
            statement = select(CourseDB).where(CourseDB.subject == subject, CourseDB.course_code == course_code).limit(1)
            sources = session.exec(statement).first()
            
            if sources == None:
                return None
            
            api_response = CourseAPIBuild(
                id=sources.id,
                subject=sources.subject, 
                course_code=sources.course_code
            )
            
            if sources.latest_attribute_id:
                result = session.get(AttributeDB, sources.latest_attribute_id)
                api_response.sqlmodel_update(result)
                
            if sources.latest_course_summary_id:
                result = session.get(CourseSummaryDB, sources.latest_course_summary_id)
                api_response.sqlmodel_update(result)
            
            if sources.latest_section_id:
                result = session.get(SectionDB, sources.latest_section_id)
                wanted_attributes = {
                    "RP" : result.RP,
                    "abbreviated_title": result.abbreviated_title,
                    "add_fees" : result.add_fees,
                    "rpt_limit" : result.rpt_limit
                }
                api_response.sqlmodel_update(wanted_attributes)
            
            # TODO: 
            # calculate availability
            # extract prerequisites
            # extract restriction
            
            # get transfers
            id = f"CRS-{subject}-{course_code}"
            statement = select(TransferDB).where(TransferDB.course_id == id)
            result = session.exec(statement).all()
            api_response.transfers = result
            
            
            # Get all sections and their schedules in one go using eager loading
            # this is dark sqlalchemy magic that was invoked by chatgpt, don't ask me how it works
            if return_offerings:

                statement = select(
                        SectionDB
                    ).where(SectionDB.subject == subject,
                    SectionDB.course_code == course_code
                    ).options(selectinload(SectionDB.schedule)
                    ).order_by(SectionDB.year.asc(), SectionDB.term.asc())
                
                results = session.exec(statement).unique()
                sections = results.all()
                
                api_response.offerings = sections

                
            
        # reset the unique id because it gets overwritten
        api_response.id = f"CRS-{subject}-{course_code}"
            
        return api_response


if __name__ == "__main__":
    
    c = Controller()
    c.create_db_and_tables()
    # c.generateCourseIndexes()
    # c.buildDatabase(use_cache=True)
    c.genIndexesAndPreBuilts()
    
    # c.updateLatestSemester()


    # sec = Section(RP=None, seats=1, crn=99999, subject="CPSC", course_code=1050, credits=3, year=2024, term=20)
    # # course = Course(RP=None, subject="CPSC", course_code=1050, credits=3, title="THIS IS A TEST, DELETE ME", description=None, hours_lecture=0, hours_lab=0, hours_seminar=0, attr_ar=False)

    # with Session(c.engine) as session:
    #     session.add(sec)
    #     session.commit()