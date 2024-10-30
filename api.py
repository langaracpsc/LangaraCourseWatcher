from contextlib import asynccontextmanager
import gzip
import json
import os
from threading import Thread
import time

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy import func
from sqlmodel import Field, Relationship, Session, SQLModel, create_engine, select

from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from enum import Enum
from typing import Annotated, Optional

from sqlmodel import Field, Session, SQLModel, col, create_engine, select
from sqlalchemy.orm import selectinload 

from Controller import Controller

# DATABASE STUFF
from sdk.schema.CourseAttribute import CourseAttributeDB
from sdk.schema.CourseOutline import CourseOutlineDB
from sdk.schema.CoursePage import CoursePage
from sdk.schema.CourseSummary import CourseSummaryDB
from sdk.schema.ScheduleEntry import ScheduleEntryDB
from sdk.schema.Section import SectionDB, SectionAPI
from sdk.schema.Transfer import TransferAPI, TransferDB

from sdk.schema.BaseModels import Course, Semester

# RESPONSE STUFF
from sdk.schema_built.ApiResponses import IndexCourse, IndexCourseList, IndexSemesterList, PaginationPage
from sdk.schema_built.CourseMax import CourseMax, CourseMaxAPI, CourseMaxAPIOnlyTransfers, CourseMaxDB


DB_LOCATION="database/database.db"
CACHE_DB_LOCATION="database/cache/cache.db"
PREBUILTS_DIRECTORY="database/prebuilts/"
ARCHIVES_DIRECTORY="database/archives/"

from dotenv import load_dotenv
load_dotenv()

from schedule import every, repeat, run_pending

# database controller
controller = Controller()

def get_session():
    with Session(controller.engine) as session:
        yield session

# === STARTUP STUFF ===

@repeat(every(20).seconds)
def hourly(use_cache: bool = False):
    c = Controller()
    c.updateLatestSemester(use_cache)


@repeat(every(24).hours)
def daily(use_cache: bool = False):
    c = Controller()
    c.buildDatabase(use_cache)
    
    # check for next semester
    c.checkIfNextSemesterExistsAndUpdate()

# have to run our scraping in a separate thread
def thread_task():
    # hourly()
    # daily()
    while True:
        run_pending()
        time.sleep(1)

thread = Thread(target=thread_task)
thread.start()

# controller.create_db_and_tables()
# hourly(use_cache=False)

# controller.create_db_and_tables()
# controller.buildDatabase(use_cache=True)

# startup()
# daily(use_cache=True)

# === FASTAPI STARTUP STUFF ===
@asynccontextmanager
async def lifespan(app: FastAPI):
        
    if not os.path.exists("database/"):
        os.mkdir("database")
        
    if not os.path.exists("database/cache"):
        os.mkdir("database/cache")

    if not os.path.exists(PREBUILTS_DIRECTORY):
        os.mkdir(PREBUILTS_DIRECTORY)

    if not os.path.exists(ARCHIVES_DIRECTORY):
        os.mkdir(ARCHIVES_DIRECTORY)


    if (os.path.exists(DB_LOCATION)):
        print("Database found.")
        controller.create_db_and_tables()
        hourly(use_cache=True)
        controller.checkIfNextSemesterExistsAndUpdate()
    else:
        print("Database not found. Building database from scratch.")
        # save results to cache if cache doesn't exist
        controller.create_db_and_tables()
        controller.buildDatabase(use_cache=True)
    yield

description = "Gets course data from the Langara website. Data refreshes hourly. All data belongs to Langara College or BC Transfer Guide and is summarized here in order to help students. Pull requests welcome!"

app = FastAPI(
    title="Langara Courses API.",
    description=description,
    redoc_url="/",
    version="1.0",
    lifespan=lifespan
    )

# gzip responses above 500 bytes
app.add_middleware(GZipMiddleware, minimum_size=500) 

origins = [
    "*",
]

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
    description="Returns the latest semester from which data is available",
    response_model=Semester
)
async def index_latest_semester(
    *,
    session: Session = Depends(get_session),
):
    
    statement = select(Semester).order_by(col(Semester.year).desc(), col(Semester.term).desc()).distinct().limit(1)
    results = session.exec(statement)
    result = results.first()
    
    return result

@app.get(
    "/index/semesters",
    summary="All semesters.",
    description="Returns all semesters from which data is available",
    response_model=IndexSemesterList
)
async def index_semesters(
    *,
    session: Session = Depends(get_session),
):
    
    statement = select(Semester
        ).order_by( col(Semester.year).desc(), col(Semester.term).desc()
        ).distinct()
    results = session.exec(statement)
    result = results.all()
    
    return IndexSemesterList(
        count = len(result),
        semesters = result
    )
        

@app.get(
    "/index/courses",
    summary="All courses.",
    description="Returns all known courses.",
    response_model=IndexCourseList
)
async def index_courses(
    *,
    session: Session = Depends(get_session),
) -> IndexCourseList:
    
    statement = select(CourseMaxDB).order_by(col(CourseMaxDB.subject).asc(), col(CourseMaxDB.course_code).asc())
    results = session.exec(statement)
    result = results.all()
    
    courses:list[IndexCourse] = []
    subjects = []
    
    for r in result:
        if r.subject not in subjects:
            subjects.append(r.subject)
        
        t = r.title
        if t == None:
            t = r.abbreviated_title
        
        c = IndexCourse(
            subject=r.subject,
            course_code=r.course_code,
            title=t,
            active=r.active
        )
        courses.append(c)
    
    return IndexCourseList(
        subject_count = len(subjects),
        course_code_count = len(courses),
        courses = courses
    )




@app.get(
    "/semester/{year}/{term}/courses",
    summary="Semester course data.",
    description="Returns all courses for a semester"
)
async def semester(
    *,
    session: Session = Depends(get_session),
    year: int, 
    term: int
) -> list[CourseMaxAPIOnlyTransfers]:
    
    # TODO: Move this to a link table instead of calculating it on the fly
    
    statement = select(SectionDB.subject, SectionDB.course_code).where(SectionDB.year == year, SectionDB.term == term).distinct()
    results = session.exec(statement)
    courses = results.all()
    
    out = []
    
    for c in courses:
        result = session.get(CourseMaxDB, f'CMAX-{c[0]}-{c[1]}')
        assert result != None
        out.append(result)
    
    return out


@app.get(
    "/semester/{year}/{term}/sections",
    summary="Semester section data.",
    description="Returns all sections of a semester",
    response_model=list[SectionAPI]
)
async def semester(
    *,
    session: Session = Depends(get_session),
    year: int, 
    term: int
) -> list[SectionAPI]:
    
    
    statement = select(SectionDB).where(
            SectionDB.year == year,
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
    response_model=CourseMaxAPI,
)
async def semesterCoursesInfo(
    *,
    session: Session = Depends(get_session),
    subject: str, 
    course_code: str
):
    subject = subject.upper()
    
    result = session.get(CourseMaxDB, f"CMAX-{subject}-{course_code}")
    
    if result == None:
        raise HTTPException(status_code=404, detail="Course not found.")
    
    return result
    

@app.get(
    "/section/{year}/{term}/{crn}",
    summary="Section information.",
    description="Get all available information for a given section.",
    response_model=SectionAPI
)
async def semesterSectionsInfo(
    *,
    session: Session = Depends(get_session),
    year: int, 
    term: int, 
    crn: int
):
    statement = select(SectionDB).where(SectionDB.year == year, SectionDB.term == term, SectionDB.crn == crn)
    results = session.exec(statement)
    section = results.first()
    
    if section == None:
        raise HTTPException(status_code=404, detail="Course not found.")
    
    statement = select(ScheduleEntryDB).where(ScheduleEntryDB.year == year, ScheduleEntryDB.term == term, ScheduleEntryDB.crn == crn)
    results = session.exec(statement)
    schedules = results.all()
    
    out = section.model_dump()
    out["schedule"] = []
    
    for s in schedules:
        out["schedule"].append(s.model_dump())
                
    return out

@app.get(
    "/transfers/{institution_code}",
    summary="Transfer information.",
    description="Get all available transfers to a given institution.",
    response_model=list[TransferAPI]
)
async def semesterSectionsInfo(
    *,
    session: Session = Depends(get_session),
    institution_code: str, 
):
    statement = select(TransferDB).where(TransferDB.destination == institution_code).order_by(col(TransferDB.credit).asc())
    results = session.exec(statement)
    transfers = results.all()
    
    if transfers == None:
        raise HTTPException(status_code=404, detail="Institution not found.")

    return transfers

# my wares are too powerful for you, traveller
@app.get(
    "/export/all",
    summary="All information.",
    description="Get all available information. You probably don't need to use this route.",
    response_model=PaginationPage
)
async def allCourses(
    *,
    session: Session = Depends(get_session),
    page:int = 1
):
    if page < 1:
        raise HTTPException(status_code=400, detail="Page number must be greater than or equal to 1")
    
    COURSES_PER_PAGE = 150

    statement = select(func.count(CourseMaxDB.id))
    total_courses = session.scalar(statement)
    
    total_pages = (total_courses + COURSES_PER_PAGE - 1) // COURSES_PER_PAGE  # Ceiling division

    if page > total_pages:
        raise HTTPException(status_code=400, detail="Page number must be equal or lesser than total_pages")
    
    statement = select(CourseMaxDB).order_by(col(CourseMaxDB.id).asc()).limit(COURSES_PER_PAGE).offset(COURSES_PER_PAGE*page-1) # 0-index page
    results = session.exec(statement)
    courses = results.all()

    p = PaginationPage(
        page=page,
        courses_per_page=COURSES_PER_PAGE,
        total_courses=total_courses,
        total_pages=total_pages,
        courses=courses
    )
    return p

# Yes, this is not a secure method for passing an authentication token
# This is extremely easy to call from firefox and it really shouldn't be called at all
# @app.get(
#     "/admin/regenerateDatabase",
#     summary="Generate the database.",
#     description="Downloads new information and builds a database.",
#     # include_in_schema=False
# )
# async def genDB(API_KEY: str) -> None:
#     if API_KEY == os.getenv("API_KEY") or os.getenv("DEBUG") == True:
#         controller.buildDatabase()
#     else:
#         return False
