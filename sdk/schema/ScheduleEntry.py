
from enum import Enum

from typing import Optional
from sqlmodel import Field, SQLModel

# TODO: reimplement enum
# enum was breaking pydantic validation for some reason
# class sectionTypes(Enum):
#     _ = " "
    
#     Lecture = "Lecture"
#     Lab = "Lab"
#     Seminar = "Seminar"
#     Practicum = "Practicum"
#     Tutorial = "Tutorial"
#     WWW = "WWW"
#     Exam = "Exam"
    
#     GIS = "GIS Guided Independent Study"
#     FA = "Flexible Assessment"
#     FS = "Field School"
#     OSW = "On Site Work"
#     EI = "Exchange-International"
#     COOP = "CO-OP(on site work experience)"

class ScheduleEntry(SQLModel):
    type: str               = Field(primary_key=True, description='Type of the section.')
    days: str               = Field(primary_key=True, description='Days of the week of the session e.g. ```M-W----```.')
    time: str               = Field(primary_key=True, description='Time session starts and ends e.g. ```1030-1220```.')
    start: Optional[str]    = Field(default=None, description='Date session starts (```YYYY-MM-DD```).')
    end: Optional[str]      = Field(default=None,  description='Date session ends (```YYYY-MM-DD```).')
    room: str               = Field(description='Room session is in.')
    instructor: str         = Field(description='Instructor(s) for this session.')
    
    class Config:
        json_schema_extra = {
            "example": {
                "type" : "Lecture",
                "days" : "M-W----",
                "time" : "1030-1220",
                "start": None,
                "end" : None,
                "room": "A136B",
                "instructor": "Bob Ross"
            }
        }
    
class ScheduleEntryDB(ScheduleEntry, table=True):
    year: int               = Field(primary_key=True, foreign_key="sectiondb.year")
    term: int               = Field(primary_key=True, foreign_key="sectiondb.term")
    crn: int                = Field(primary_key=True, foreign_key="sectiondb.crn")

class ScheduleEntryAPI(ScheduleEntry):
    pass