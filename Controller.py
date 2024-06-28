
import json
import time
from typing import TYPE_CHECKING

from sqlalchemy import union

PREBUILTS_DIRECTORY="database/prebuilts/"

from sdk.schema.BaseModels import Course, Semester
from sdk.schema.CourseAttribute import CourseAttributeDB
from sdk.schema.CourseOutline import CourseOutlineDB
from sdk.schema.CoursePage import CoursePageDB
from sdk.schema.CourseSummary import CourseSummaryDB
from sdk.schema.Section import SectionAPI, SectionDB
from sdk.schema.ScheduleEntry import ScheduleEntryDB
from sdk.schema.Transfer import Transfer, TransferDB

from sqlmodel import Field, Session, SQLModel, create_engine, select, col
from sqlalchemy.orm import selectinload 
from pydantic.json import pydantic_encoder

from sdk.schema_built.CourseMax import CourseMax, CourseMaxDB
from sdk.scrapers.DownloadLangaraInfo import fetchTermFromWeb
from sdk.parsers.SemesterParser import parseSemesterHTML
from sdk.parsers.CatalogueParser import parseCatalogueHTML
from sdk.parsers.AttributesParser import parseAttributesHTML
from sdk.scrapers.DownloadTransferInfo import getTransferInformation
from sdk.scrapers.LangaraCourseIndex import getCoursePageInfo
from sdk.scrapers.ScraperUtilities import createSession


class Controller():    
    def __init__(self, db_path="database/database.db", db_type="sqlite") -> None:        
        connect_args = {"check_same_thread": False}
        self.engine = create_engine(f"{db_type}:///{db_path}", connect_args=connect_args)
        
        self.existing_courses:dict[str, list[int]] = {}
        
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
    def updateLatestSemester(self, use_cache=False):
         
        latestSemester = Controller.getLatestSemester(self.engine)       
        assert latestSemester != None, "Database is empty!"
        
        year = latestSemester[0]
        term = latestSemester[1]
        
        changes = self.updateSemester(year, term, use_cache)
        self.genIndexesAndPreBuilts()
        
        # now = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        # print(f"[{now}] Fetched new data from Langara. {len(changes)} changes found.")
        return changes

    
    # Build the entire database from scratch.
    # Takes approximately 45 minutes from a live connection
    def buildDatabase(self, use_cache=False):
        print("Building database...\n")
        start = time.time()        
        
        
        
        # Download, parse and save Transfer Information
        # Takes 20-30 minutes from live and 20 seconds from cache.
        print("=== FETCHING TRANSFER INFORMATION ===")
        self.fetchParseSaveTransfers(use_cache)
        timepoint1 = time.time()
        print(f"Transfer information downloaded and parsed in {Controller.timeDeltaString(start, timepoint1)}")    
        print()
        
        # DPS course pages from the main langara website
        # Takes ?? from live and about a minute from cache.
        print("=== FETCHING COURSE PAGES INFORMATION ===")
        self.fetchParseSaveCoursePages(use_cache)
        timepoint2 = time.time()
        print(f"Langara course page information downloaded and parsed in {Controller.timeDeltaString(timepoint1, timepoint2)}")

        
        # Download, parse and save Langara Tnformation
        # Takes 20-30 minutes from live and 10 - 5 minutes from cache
        print("=== FETCHING SEMESTERLY INFORMATION ===")
        
        year, term = 1999, 20 # oldest records available on Banner
        out = True
        
        while out:
            out = self.updateSemester(year, term, use_cache)
            year, term = Controller.incrementTerm(year, term)
            
        timepoint3 = time.time()
        print(f"Langara sections downloaded and parsed in {Controller.timeDeltaString(timepoint2, timepoint3)}")
        print()
        
        # Takes approximately 3 minutes
        print("=== GENERATING AGGREGATIONS & PREBUILTS ===")
        self.genIndexesAndPreBuilts()
        timepoint4 = time.time()
        print(f"Database indexes built in {Controller.timeDeltaString(timepoint3, timepoint4)}") 
        print()
        
        
        print(f"Database built in {Controller.timeDeltaString(start, timepoint4)}!")
    
    def fetchParseSaveCoursePages(self, use_cache):
        web_session = createSession("database/cache/cache.db", use_cache)
        courses, outlines = getCoursePageInfo(web_session)
        
        with Session(self.engine) as session:
            for c in courses:
                self.checkCourseExists(session, c.subject, c.course_code, c)
                
                result = session.get(CoursePageDB, c.id)
                                
                # insert if it doesn't exist or update if it does exist
                if result == None:
                    session.add(c)
                else:
                    new_data = c.model_dump()
                    result.sqlmodel_update(new_data)
                    session.add(result)
            
            for o in outlines:                
                result = session.get(CourseOutlineDB, o.id)
                                
                # insert if it doesn't exist or update if it does exist
                if result == None:
                    session.add(o)
                else:
                    new_data = o.model_dump()
                    result.sqlmodel_update(new_data)
                    session.add(result)
            
            session.commit()
        
        print(f"Saved {len(courses)} courses to the database.")
    

    class SemesterInternal(SQLModel):
        year: int               = Field(description='Year of semester e.g. ```2024```.')
        term: int               = Field(description='Term of semester e.g. ```30```.')
        
        attributes: list[CourseAttributeDB]           = Field(default=[])
        courseSummaries: list[CourseSummaryDB]  = Field(default=[])
        sections: list[SectionDB]               = Field(default=[], description='List of sections in the semester.')
        schedules: list[ScheduleEntryDB]        = Field(default=[])
    
    # gets data that is by semester
    # sections, catalogue, and attributes
    # returns true when the semester is updated or None if it can't find data for the given semester
    def updateSemester(self, year:int, term:int, use_cache:bool=False) -> bool | None:
        
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
        # TODO: this is horribly slow - it needs a rewrite/optimizations
        # how do you implement an UPSERT in SQLModel???
        with Session(self.engine) as session:
            
            # save Semester if it doesn't exist
            statement = select(Semester).where(Semester.year==year, Semester.term==term)
            results = session.exec(statement)
            result = results.first()
            
            if result == None:
                s = Semester(
                    id=f'SMTR-{year}-{term}',
                    year=year,
                    term=term
                )
                session.add(s)
                
            # TODO: move changes watcher to its own service
            
            for c in warehouse.sections:
                self.checkCourseExists(session, c.subject, c.course_code, c)
                
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
                self.checkCourseExists(session, cs.subject, cs.course_code, cs)
                
                result = session.get(CourseSummaryDB, cs.id)
                
                # insert if it doesn't exist or update if it already exists
                if result == None:
                    session.add(cs)
                else:
                    new_data = cs.model_dump()
                    result.sqlmodel_update(new_data)
                    session.add(result)
            
            for a in warehouse.attributes:
                self.checkCourseExists(session, a.subject, a.course_code, a)
                result = session.get(CourseAttributeDB, a.id)
                
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
    
    def checkCourseExists(self, session:Session, subject:str, course_code:int, obj) -> None:
        if type(subject) != str:
            print("BAD!!!!")
            print(obj)
            print(subject, course_code)
            input()
        # check in-memory index before going out to the database
        # performance impact not tested but I/O is always slow
        if subject in self.existing_courses and course_code in self.existing_courses["subject"]:
            return
    
        statement = select(Course).where(Course.subject == subject, Course.course_code == course_code).limit(1)
        results = session.exec(statement)
        result = results.first()
        
        if result == None:
            # CRSE-ENGL-1123
            c = Course(id=f'CRSE-{subject}-{course_code}', subject=subject, course_code=course_code)
            session.add(c)
        
        # save to index if course doesn't exist in index already
        if subject in self.existing_courses:
            self.existing_courses["subject"].append(course_code)
        else:
            self.existing_courses["subject"] = [course_code]
            
    
    def fetchParseSaveTransfers(self, use_cache):
        transfers = getTransferInformation(use_cache=use_cache)
        
        with Session(self.engine) as session:
            for i, t in enumerate(transfers):
                
                self.checkCourseExists(session, t.subject, t.course_code, t)
                
                result = session.get(TransferDB, t.id)
                
                # insert if it doesn't exist or update if it already exists
                if result == None:
                    session.add(t)
                else:
                    new_data = t.model_dump()
                    result.sqlmodel_update(new_data)
                    session.add(result)
                
                if i % 5000==0:
                    print(f"Storing transfer agreements... ({i}/{len(transfers)})")
            
            session.commit()
                

    
    def genIndexesAndPreBuilts(self) -> None:
        self._generateCourseIndexes()
        self._generatePreBuilds()
    
    # generate the Course
    def _generateCourseIndexes(self) -> None:
        # get list of courses
        with Session(self.engine) as session:
            statement = select(Course.subject, Course.course_code).distinct()
            results = session.exec(statement)
            courses = results.all() 
            
            # print(courses)
            
            i = 0
            
            for subject, course_code in courses:
                if i % 500 == 0:
                    print(f"Generating course summaries... ({i}/{len(courses)+1})")
                i+=1
                    
                c = CourseMaxDB(
                    id=f"CMAX-{subject}-{course_code}",
                    subject=subject, 
                    course_code=course_code
                )
                
                """
                The purpose of the following code is to get the freshest values where they exist
                So we want the latest fees, the latest course description, etc.
                This takes quite a bit of effort to build...
                """
                
                course_summary_possibly_old = None
                statement = select(CourseSummaryDB).where(
                    CourseSummaryDB.subject == subject, 
                    CourseSummaryDB.course_code == course_code
                    ).order_by(col(CourseSummaryDB.year).desc(), col(CourseSummaryDB.term).desc()).limit(1)
                results = session.exec(statement)
                r = session.exec(statement).first()
                if r:
                    c.credits = r.credits
                    c.title = r.title
                    c.description = r.description
                    c.hours_lecture = r.hours_lecture
                    c.hours_seminar = r.hours_seminar
                    c.hours_lab = r.hours_lab
                    
                    course_summary_possibly_old = r
                
                # CoursePage
                # We replace the attributes from CourseSummary because
                # CourseSummary has information for some discontinued courses 
                statement = select(CoursePageDB).where(
                    CoursePageDB.subject == subject, 
                    CoursePageDB.course_code == course_code
                    ).limit(1)
                results = session.exec(statement)
                r = session.exec(statement).first()
                if r != None:
                    c.active = True
                    c.title = r.title
                    c.description = r.description
                    c.desc_duplicate_credit = r.desc_duplicate_credit
                    c.desc_registration_restriction = r.desc_registration_restriction
                    c.desc_prerequisite = r.desc_prerequisite
                    c.desc_replacement_course = r.desc_replacement_course
                    
                    c.credits = r.credits
                    c.hours_lecture = r.hours_lecture
                    c.hours_seminar = r.hours_seminar
                    c.hours_lab = r.hours_lab
                    
                    # c.university_transferrable = r.university_transferrable
                    c.offered_online = r.offered_online
                    c.preparatory_course = r.preparatory_course
                else:
                    c.active = False
                    if course_summary_possibly_old != None:
                        r = course_summary_possibly_old
                        if r.description != None and r.desc_last_updated != None:
                            c.description = r.description + "\n\n" + r.desc_last_updated
                        c.desc_replacement_course = r.desc_replacement_course
                        c.desc_prerequisite = r.desc_requisites
                    
                
                statement = select(CourseAttributeDB).where(
                    CourseAttributeDB.subject == subject,
                    CourseAttributeDB.course_code == course_code
                ).order_by(col(CourseAttributeDB.year).desc(), col(CourseAttributeDB.term).desc()).limit(1) 
                r = session.exec(statement).first()
                if r:
                    c.attr_ar = r.attr_ar
                    c.attr_sc = r.attr_sc
                    c.attr_hum = r.attr_hum
                    c.attr_lsc = r.attr_lsc
                    c.attr_sci = r.attr_sci
                    c.attr_soc = r.attr_soc
                    c.attr_ut = r.attr_ut
                    
                    
                statement = select(SectionDB).where(
                    SectionDB.subject == subject, 
                    SectionDB.course_code == course_code
                    ).order_by(col(SectionDB.year).desc(), col(SectionDB.term).desc()
                    ).limit(1)
                    
                results = session.exec(statement)
                r = session.exec(statement).first()
                if r:
                    c.RP = r.RP
                    c.abbreviated_title = r.abbreviated_title
                    c.add_fees = r.add_fees
                    c.rpt_limit = r.rpt_limit
                    
                
                if c.title == None or c.credits == None:
                    statement = select(TransferDB).where(
                        TransferDB.subject == subject, 
                        TransferDB.course_code == course_code,
                        )
                        
                    results = session.exec(statement)
                    results = session.exec(statement).all()
                    for r in results:
                        if r.source_title != None and c.title == None:
                            c.title = r.source_title
                        if r.source_credits != None and c.credits == None:
                            c.credits = r.source_credits                    
                
                # generate some aggregate values
                statement = select(SectionDB).where(
                    SectionDB.subject == subject, 
                    SectionDB.course_code == course_code
                    ).order_by(col(SectionDB.year).desc(), col(SectionDB.term).desc()
                    ).limit(1)
                r = session.exec(statement).first()
                if r:
                    c.last_offered_year = r.year
                    c.last_offered_term = r.term
                    
                    statement = select(SectionDB).where(
                        SectionDB.subject == subject, 
                        SectionDB.course_code == course_code
                        ).order_by(col(SectionDB.year).asc(), col(SectionDB.term).asc()
                        ).limit(1)
                    r = session.exec(statement).first()
                    
                    c.first_offered_year = r.year
                    c.first_offered_term = r.term
                
                
                # save CourseMax to the database once we are done
                
                result = session.get(CourseMaxDB, c.id)
                # insert if it doesn't exist or update if it already exists
                if result == None:
                    session.add(c)
                else:
                    new_data = c.model_dump()
                    result.sqlmodel_update(new_data)
                    session.add(result)
                    
                    
                session.commit()
    
    def _generatePreBuilds(self) -> None:    
        
        out = []

        # get all courses for the given semester
        with Session(self.engine) as session:
            statement = select(Course.subject, Course.course_code).distinct()
            results = session.exec(statement)
            courses = results.all() 
            
        # for c in courses:
        #     out.append(self.buildCourse(c[0], c[1], return_offerings=True))
        
        # with open(PREBUILTS_DIRECTORY + "allInfo.json", "w+") as fi:
        #     fi.write(json.dumps(out, default=pydantic_encoder))   
        
        
        
        
    # def buildCourse(self, subject, course_code, return_offerings=True) -> CourseAPIBuild | None:
                
    #     with Session(self.engine) as session:
            
    #         statement = select(CourseBuiltDB).where(CourseBuiltDB.subject == subject, CourseBuiltDB.course_code == course_code).limit(1)
    #         sources = session.exec(statement).first()
            
    #         if sources == None:
    #             return None
            
    #         api_response = CourseAPIBuild(
    #             id=sources.id,
    #             subject=sources.subject, 
    #             course_code=sources.course_code
    #         )
            
    #         if sources.latest_attribute_id:
    #             result = session.get(CourseAttributeDB, sources.latest_attribute_id)
    #             api_response.sqlmodel_update(result)
                
    #         if sources.latest_course_summary_id:
    #             result = session.get(CourseSummaryDB, sources.latest_course_summary_id)
    #             api_response.sqlmodel_update(result)
            
    #         if sources.latest_section_id:
    #             result = session.get(SectionDB, sources.latest_section_id)
    #             wanted_attributes = {
    #                 "RP" : result.RP,
    #                 "abbreviated_title": result.abbreviated_title,
    #                 "add_fees" : result.add_fees,
    #                 "rpt_limit" : result.rpt_limit
    #             }
    #             api_response.sqlmodel_update(wanted_attributes)
    #             api_response.last_offered_year = result.year
    #             api_response.last_offered_term = result.term
                
    #             statement = select(
    #                 SectionDB.year, SectionDB.term
    #                 ).order_by(
    #                     col(SectionDB.year).asc(), 
    #                     col(SectionDB.term).asc()
    #                     ).limit(1) 
    #             result = session.exec(statement).first()
    #             api_response.first_offered_year = result[0]
    #             api_response.first_offered_term = result[1]
            
    #         # TODO: 
    #         # calculate availability
    #         # extract prerequisites
    #         # extract restriction
            
    #         # get transfers
    #         id = f"CRS-{subject}-{course_code}"
    #         statement = select(TransferDB).where(TransferDB.course_id == id)
    #         result = session.exec(statement).all()
    #         api_response.transfers = result
            
            
    #         # Get all sections and their schedules in one go using eager loading
    #         # this is dark sqlalchemy magic that was invoked by chatgpt, don't ask me how it works
    #         if return_offerings:

    #             statement = select(
    #                     SectionDB
    #                 ).where(SectionDB.subject == subject,
    #                 SectionDB.course_code == course_code
    #                 ).options(selectinload(SectionDB.schedule)
    #                 ).order_by(SectionDB.year.asc(), SectionDB.term.asc())
                
    #             results = session.exec(statement).unique()
    #             sections = results.all()
                
    #             api_response.offerings = sections

                
            
    #     # reset the unique id because it gets overwritten
    #     api_response.id = f"CRS-{subject}-{course_code}"
            
    #     return api_response


if __name__ == "__main__":
    
    # c = Controller()
    # c.create_db_and_tables()
    # c.buildDatabase(use_cache=False)
    # c.genIndexesAndPreBuilts()
    
    # nonce = "7c0c2d0f29"
    transfers = getTransferInformation(use_cache=False)
    
    # c.updateLatestSemester()