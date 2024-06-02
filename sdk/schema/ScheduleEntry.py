
from enum import Enum

from typing import Optional, TYPE_CHECKING
from sqlmodel import Field, Relationship, SQLModel

# from sdk.schema.Section import SectionDB

if TYPE_CHECKING:
    from sdk.schema.Section import SectionDB
    
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
    type: str               = Field(description='Type of the section.')
    days: str               = Field(description='Days of the week of the session e.g. ```M-W----```.')
    time: str               = Field(description='Time session starts and ends e.g. ```1030-1220```.')
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
    id: str                 = Field(primary_key=True, description="Unique identifier for a ScheduleEntry.")
    
    section_id: Optional[str] = Field(default=None, index=True, foreign_key="sectiondb.id")
    section: Optional["SectionDB"] = Relationship(back_populates="schedule")
    
    year: int               = Field(index=True)
    term: int               = Field(index=True)
    crn: int                = Field(index=True)

class ScheduleEntryAPI(ScheduleEntry):
    id: str