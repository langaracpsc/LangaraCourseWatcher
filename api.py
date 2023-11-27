import json

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from main import DB_EXPORT_LOCATION


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
    response_class=FileResponse,
    summary="Returns all courses and transfer agreements.",
    description="Returns an SQLite database containing all courses and transfer agreements at Langara College."
    )
async def get_semester_courses():
    path = DB_EXPORT_LOCATION
    response = FileResponse(path)

    # DO NOT CACHE RESPONSE
    response.headers["Cache-Control"] = "no-store, max-age=0"

    return response