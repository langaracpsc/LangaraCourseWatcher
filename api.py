from contextlib import asynccontextmanager
import gzip

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse

from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from enum import Enum
from typing import Annotated, Optional

from sqlmodel import Field, Session, SQLModel, col, create_engine, select
from sqlalchemy.orm import selectinload 

from Controller import Controller

from sdk.schema.Attribute import Attribute, AttributeDB
from sdk.schema.CourseSummary import CourseSummaryDB

from sdk.schema.Section import SectionDB, SectionAPI
from sdk.schema.ScheduleEntry import ScheduleEntry, ScheduleEntryDB, ScheduleEntryAPI
from sdk.schema.Transfer import Transfer

from sdk.schema_built.Course import CourseAPI, CourseAPIExt, CourseBase, CourseAPIBuild
from sdk.schema_built.Semester import Semester, SemesterCourses, SemesterSections

from main import DB_EXPORT_LOCATION, DB_LOCATION

from dotenv import load_dotenv
load_dotenv()


# database controller
controller = Controller()




@asynccontextmanager
async def lifespan(app: FastAPI):
    # called when the api is turned on
    controller.create_db_and_tables()
    # TODO: implement refresh stuff
    yield
    # any teardown code to be run when the code exits


origins = [
    "*",
]

# better api stuff
description = "Gets course data from the Langara website. Data refreshes hourly. All data belongs to Langara College or BC Transfer Guide and is summarized here in order to help students. Pull requests welcome!"

app = FastAPI(
    title="Langara Courses API.",
    description=description,
    redoc_url="/",
    version="1.0",
    lifespan=lifespan
    )

app.add_middleware(GZipMiddleware, minimum_size=500) # only gzip responses above 500 bytes

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==== ROUTES ====
@app.get(
    "/index/latest_semester",
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
    "/index/all_semesters",
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
    "/index/all_subjects",
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
    "/index/all_courses",
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
async def semester(year:int, term:int) -> list[CourseAPI]:
    # check that year/term exist
    
    api_response = []

    # get all courses for the given semester
    with Session(controller.engine) as session:
        statement = select(SectionDB.subject, SectionDB.course_code).where(SectionDB.year == year, SectionDB.term == term).distinct()
        results = session.exec(statement)
        courses = results.all()
    
    for c in courses:
        api_response.append(controller.buildCourse(c[0], c[1], return_offerings=False))
    
    return api_response


@app.get(
    "/semester/sections/{year}/{term}",
    summary="Semester data.",
    description="Returns all sections of a semester",
    response_model=list[SectionAPI]
)
async def semester(year:int, term:int) -> list[SectionAPI]:
    
    with Session(controller.engine) as session:
        
        statement = select(
                SectionDB
            ).where(SectionDB.year == year,
            SectionDB.term == term
            ).options(selectinload(SectionDB.schedule)
            ).order_by(SectionDB.year.asc(), SectionDB.term.asc())
        
        results = session.exec(statement).unique()
        sections = results.all()
        
        return sections


@app.get(
    "/course/{subject}/{course_code}",
    summary="Course information.",
    description="Get all available information for a given course.",
    response_model=CourseAPIExt,
    
)
async def courseInfo(subject: str, course_code:int):
    subject = subject.upper()
    
    c = controller.buildCourse(subject, course_code, True)
    
    if c == None:
        raise HTTPException(status_code=404, detail="Course not found")
    
    return c
    

@app.get(
    "/section/{year}/{term}/{crn}",
    summary="Section information.",
    description="Get all available information for a given section.",
    response_model=SectionAPI
)
async def courseInfo(year: int, term:int, crn: int):
     with Session(controller.engine) as session:
        statement = select(SectionDB).where(SectionDB.year == year, SectionDB.term == term, SectionDB.crn == crn)
        results = session.exec(statement)
        section = results.first()
        
        if section == None:
            return 404 
        
        statement = select(ScheduleEntryDB).where(ScheduleEntryDB.year == year, ScheduleEntryDB.term == term, ScheduleEntryDB.crn == crn)
        results = session.exec(statement)
        schedules = results.all()
        
        out = section.model_dump()
        out["schedule"] = []
        
        for s in schedules:
            out["schedule"].append(s.model_dump())
            
        # print(out)
        
        return out
        
