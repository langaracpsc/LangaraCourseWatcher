import gzip
import json

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse

from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from python.main import DB_EXPORT_LOCATION, DB_LOCATION

from LangaraCourseInfo import Database, Utilities, Course

import os
from dotenv import load_dotenv
load_dotenv()

description = "Gets course data from the Langara website. Data refreshes hourly. All data belongs to Langara College or BC Transfer Guide and is summarized here in order to help students. Pull requests welcome!"

app = FastAPI(
    title="Langara Courses API.",
    description=description,
    redoc_url="/"
    )

origins = [
    "*",
]

# app.add_middleware(GZipMiddleware, minimum_size=500) # only gzip responses above 500 bytes

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.get(
    "/courseDB.db", 
    summary="Returns all courses and transfer agreements.",
    description="Returns an SQLite database containing all courses and transfer agreements at Langara College."
)
async def get_semester_courses():
    path = "database/LangaraCourseInfoExport.db.gz"

    response = FileResponse(path)
    response.headers["Content-Encoding"] = "gzip"

    return response

@app.get(
    "/data/{subject}"
) 
async def get_subject_courses(subject:str) -> list[int]:
    subject = subject.upper()
    
    db = Database(DB_EXPORT_LOCATION)
    u = Utilities(db)
    courses = db.cursor.execute("SELECT course_code FROM CourseInfo WHERE subject=?", (subject,))
    courses = courses.fetchall()
    
    # format from a list of single item tuples to a simple list
    courses = [course[0] for course in courses]
    
    return courses




@app.get(
    "/data/{subject}/{course_code}",
) 
async def get_course_info(subject:str, course_code:int) -> dict:
    subject = subject.upper()

    db = Database(DB_EXPORT_LOCATION)
    u = Utilities(db)
    
    course = db.cursor.execute("SELECT * FROM CourseInfo WHERE subject=? AND course_code=?", (subject, course_code))
    course = course.fetchone()
    if course == None:
        raise HTTPException(status_code=404, detail=f"Course not found.")
    
    c = course    
    course = {
        "subject" : c[0],
        "course_code": c[1],
        "credits" : c[2],
        "title" : c[3],
        "description" : c[4],
        "lecture_hours" : c[5],
        "seminar_hours" : c[6],
        "lab_hours" : c[7],
        "AR" : c[8],
        "SC" : c[9],
        "HUM" : c[10],
        "LSC" : c[11],
        "SCI" : c[12],
        "SOC" : c[13],
        "UT" : c[14]
    }
    
    transfers = db.cursor.execute("SELECT * FROM TransferInformation WHERE subject=? AND course_code=?", (subject, course_code))
    transfers = transfers.fetchall()
    
    all_courses = db.cursor.execute("SELECT * FROM Sections WHERE subject=? AND course_code=?", (subject, course_code))
    all_courses = all_courses.fetchall()
    
    all_courses_better:list[Course] = []
    for c in all_courses:
        real_c = Course(RP=c[2], seats=c[3], waitlist=c[4], crn=c[5], subject=c[6], course_code=c[7], section=c[8], credits=c[9], title=c[10], add_fees=c[11], rpt_limit=c[12], notes=c[13], schedule=[])
        real_c = real_c.model_dump()
        
        real_c["year"] = c[0]
        real_c["term"] = c[1]
        real_c["schedule"] = db.getSchedules(c[0], c[1], c[5])
        all_courses_better.append(real_c)
        

    return {
        "courseInfo" : course,
        "transfers" : transfers,
        "offerings" : all_courses_better
    }
                    
    
@app.get(
    "/data/{year}/{term}/{crn}",
    summary="Get information for one specific section of a course."
) 
async def get_section(year:int, term:int, crn:int) -> Course:
    
    db = Database(DB_EXPORT_LOCATION)
    u = Utilities(db)
    
    section = u.db.getSection(year, term, crn)
    
    return section

class Semester:
    year: int
    term: int
    
    class Config:
        schema_extra = {
            "example": {
                "year": 2024,
                "term" : 10,
            }
        }

@app.get(
    "data/current_semester",
    summary="Returns the current year and semester (yes this is subjective)."
)
async def current_semester() -> Semester:
    # TODO: make this dynamic
    return Semester(2024, 20)

@app.get(
    "/update/{year}/{term}",
    summary="Update semester data.",
    description="Attempts to update data for the given semester.",
    include_in_schema=False
)
async def update_semester(year, term):
    
    if not os.getenv("DEBUG_MODE"):
        return 401
    
    try:
        db = Database(DB_LOCATION)
        u = Utilities(db)
        
        from LangaraCourseInfo import fetchTermFromWeb, parseSemesterHTML
        term = fetchTermFromWeb(year, term)
            
        semester = parseSemesterHTML(term[2])
        
        u.db.insertSemester(semester)
        u.db.insertLangaraHTML(term[0], term[1], term[2], term[3], term[4])
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=e)
    
    return 200
    
@app.get(
    "/misc/force_export",
    summary="Force database export.",
    description="Forces the database to be exported for API use.",
    include_in_schema=False
)
async def force_export():
    
    if not os.getenv("DEBUG_MODE"):
        return 401
    
    db = Database(DB_LOCATION)
    u = Utilities(db)
    u.exportDatabase(DB_EXPORT_LOCATION)
    
    # prezip export
    with open(DB_EXPORT_LOCATION, 'rb') as f_in:
        with gzip.open(DB_EXPORT_LOCATION + ".gz", 'wb') as f_out:
            f_out.writelines(f_in)
                    

# @app.get(
#     "/{subject}/{course_code}",
#     response_class=HTMLResponse,
#     summary="Returns all known information about a course."
# )
# async def return_course_info(subject, course_code):
    
#     return """
#         <h1>Coming soon!</h1>
#     """