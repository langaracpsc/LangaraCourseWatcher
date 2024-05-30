from contextlib import asynccontextmanager
import gzip

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse

from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from enum import Enum
from typing import Annotated, Optional

from sqlmodel import Field, Session, SQLModel, col, create_engine, select


from Controller import Controller

from sdk.schema.Attribute import AttributeDB
from sdk.schema.CourseSummary import CourseSummaryDB

from sdk.schema.Section import SectionDB, SectionAPI
from sdk.schema.ScheduleEntry import ScheduleEntry, ScheduleEntryDB, ScheduleEntryAPI
from sdk.schema.Transfer import Transfer

from sdk.schema_built.Course import CourseAPI
from sdk.schema_built.Semester import Semester, SemesterCourses, SemesterSections

from main import DB_EXPORT_LOCATION, DB_LOCATION

from dotenv import load_dotenv
load_dotenv()


# database controller
controller = Controller()


# better api stuff
description = "Gets course data from the Langara website. Data refreshes hourly. All data belongs to Langara College or BC Transfer Guide and is summarized here in order to help students. Pull requests welcome!"

app = FastAPI(
    title="Langara Courses API.",
    description=description,
    redoc_url="/",
    version="1.0"
    )

origins = [
    "*",
]

app.add_middleware(GZipMiddleware, minimum_size=500) # only gzip responses above 500 bytes

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # called when the api is turned on
    controller.create_db_and_tables()
    # TODO: implement refresh stuff
    yield
    # any teardown code to be run when the code exits

# ==== ROUTES ====
@app.get(
    "/misc/latest_semester",
    summary="Latest semester.",
    description="Returns the latest semester from which data is available"
)
async def semesters_all() -> dict[str, int]:
    with Session(controller.engine) as session:
        statement = select(CourseSummaryDB.year, CourseSummaryDB.term).order_by(col(CourseSummaryDB.year).desc(), col(CourseSummaryDB.term).desc()).distinct().limit(1)
        results = session.exec(statement)
        result = results.all()
        
        return {
            "year": result[0][0], 
            "term": result[0][1]
        }
        

@app.get(
    "/misc/all_semesters",
    summary="All semesters.",
    description="Returns all semesters from which data is available"
)
async def semesters_all() -> list[str]:
    with Session(controller.engine) as session:
        statement = select(CourseSummaryDB.year, CourseSummaryDB.term).order_by(col(CourseSummaryDB.year).desc(), col(CourseSummaryDB.term).desc()).distinct()
        results = session.exec(statement)
        result = results.all()
        
        # looks cleaner but creates more work on the frontend!
        formatted = []
        for c in result:
            formatted.append(f"{c[0]} {c[1]}")
        return formatted
            

@app.get(
    "/misc/all_subjects",
    summary="All subjects.",
    description="Returns all known subjects."
)
async def subjects_all() -> list[str]:
        
    with Session(controller.engine) as session:
        statement = select(CourseSummaryDB.subject).distinct()
        results = session.exec(statement)
        result = results.all()
        
        return result
        


@app.get(
    "/misc/all_courses",
    summary="All courses.",
    description="Returns all known courses."
)
async def courses_all() -> list[str]: #list[tuple[str, int]]:
    
    with Session(controller.engine) as session:
        statement = select(CourseSummaryDB.subject, CourseSummaryDB.course_code).distinct()
        results = session.exec(statement)
        result = results.all()

        # looks cleaner but creates more work on the frontend!
        formatted = []
        for c in result:
            formatted.append(f"{c[0]} {c[1]}")
        return formatted
        
        


@app.get(
    "/semester/courses/{year}/{term}",
    summary="Semester data.",
    description="Returns all information available for a semester"
)
async def semester(year:int, term:int) -> SemesterCourses:
    return 504

    # this is a handful
    s = SemesterCourses()
    
    with Session(controller.engine) as session:
        statement = select(CourseSummaryDB.subject, CourseSummaryDB.course_code).distinct()
        results = session.exec(statement)
        result = results.all()


@app.get(
    "/semester/sections/{year}/{term}",
    summary="Semester data.",
    description="Returns all information available for a semester",
    response_model=list[SectionAPI]
)
async def semester(year:int, term:int) -> list[SectionAPI]:
    # semester = SemesterSections(year=year, term=term)
    
    with Session(controller.engine) as session:
        statement = select(SectionDB).where(SectionDB.year == year, SectionDB.term == term).distinct()
        results = session.exec(statement)
        result = results.all()
        
        print(result[0])
        
        # out = []
        
        # for section in result:
            
            
        #     # get the schedules for the section
        #     statement = select(ScheduleEntryDB).where(ScheduleEntryDB.year == year, ScheduleEntryDB.term == term, ScheduleEntryDB.crn == section.crn)
        #     results = session.exec(statement)
        #     result = results.all()
        #     assert result != None
            
            
        # s.sections = result
    return result
    semester.sections = result
    return semester



# @app.get(
#     "{year}/{term}/{subject}",
#     summary="Semester information by subject.",
#     description="Returns all information for a given subject within a given semester"
# )
# async def semester_subject() -> Semester:
#     return 501


@app.get(
    "/course/{subject}/{course_code}",
    summary="Course information.",
    description="Get all available information for a given course."
)
async def courseInfo(subject: str, course_code:int) -> CourseAPI:
    return 501


@app.get(
    "/section/{year}/{term}/{crn}",
    summary="Section information.",
    description="Get all available information for a given section."
)
async def courseInfo(subject: str, course_code:int, crn: int) -> SectionAPI:
    return 501