from enum import Enum
from typing import Optional
from sqlmodel import Field, SQLModel


class CourseSummary(SQLModel):
    subject: str                = Field(description="Subject area e.g. ```CPSC```.")
    course_code: int            = Field(description="Course code e.g. ```1050```.")   
    
    credits: float              = Field(description="Credits the course is worth.")
    
    title: str                  = Field(description="*Unabbreviated* title of the course e.g. ```Intro to Computer Science```.")
    description: Optional[str]  = Field(description="Description of course.")
    
    hours_lecture: float          = Field(default=False, description="Lecture hours of the course.")
    hours_seminar: float          = Field(default=False, description="Lecture hours of the course.")
    hours_lab: float              = Field(default=False, description="Lecture hours of the course.")
    

class CourseSummaryDB(CourseSummary, table=True):
    id: str                     = Field(primary_key=True, description="Unique identifier for each CourseSummary.")
    year: int                   = Field(description='Year e.g. ```2024```.')
    term: int                   = Field(description='Term e.g. ```30```')