import json

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware


desc = "Gets course data from the Langara website. Data refreshes hourly. All data belongs to Langara College or BC Transfer Guide and is summarized here in order to help students. Pull requests welcome!"

app = FastAPI(
    title="Langara Courses API.",
    description=desc,
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



@app.get(
    "/courseDB.db", 
    summary="Returns all courses and transfer agreements.",
    description="Returns an SQLite database containing all courses and transfer agreements at Langara College."
    )
async def get_semester_courses():
    path = "LangaraCourseInfoExport.db"
    return FileResponse(path)