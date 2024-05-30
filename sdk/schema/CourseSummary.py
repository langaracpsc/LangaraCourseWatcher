from enum import Enum
from typing import Optional
from sqlmodel import Field, SQLModel


class CourseSummary(SQLModel):
    subject: str                = Field(primary_key=True, description="Subject area e.g. ```CPSC```.")
    course_code: int            = Field(primary_key=True, description="Course code e.g. ```1050```.")   
    
    credits: float              = Field(description="Credits the course is worth.")
    
    title: str                  = Field(description="*Unabbreviated* title of the course e.g. ```Intro to Computer Science```.")
    description: Optional[str]  = Field(description="Description of course.")
    
    hours_lecture: int          = Field(default=False, description="Lecture hours of the course.")
    hours_seminar: int          = Field(default=False, description="Lecture hours of the course.")
    hours_lab: int              = Field(default=False, description="Lecture hours of the course.")
    

class CourseSummaryDB(CourseSummary, table=True):
    year: int                   = Field(primary_key=True, description='Year e.g. ```2024```.')
    term: int                   = Field(primary_key=True, description='Term e.g. ```30```')