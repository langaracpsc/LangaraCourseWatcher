from enum import Enum
from typing import Optional, Union
from sqlmodel import Field, Relationship, SQLModel

from sdk.schema.ScheduleEntry import ScheduleEntry


class RPEnum(Enum):
    R = "R"
    P = "P"
    RP = "RP"

class SectionBase(SQLModel):
    crn: int                        = Field(primary_key=True, description="Always 5 digits long.")
    
    RP : Optional[RPEnum]           = Field(description='Prerequisites of the course.')
    seats: Optional[str]            = Field(description='```"Inact"``` means registration isn\'t open yet. \n\n```"Cancel"``` means that the course is cancelled.')
    waitlist: Optional[str]         = Field(description='```null``` means that the course has no waitlist (ie MATH 1183 & MATH 1283). \n\n```"N/A"``` means the course does not have a waitlist.')
    subject: str                    = Field(description="Subject area e.g. ```CPSC```.")
    course_code: int                = Field(description="Course code e.g. ```1050```.")
    section: Optional[str]          = Field(description="Section e.g. ```001```, ```W01```, ```M01```.")
    credits: float                  = Field(description="Credits the course is worth.")
    title: Optional[str]            = Field(description="Abbreviated title of the course e.g. ```Algrthms & Data Strctrs I```.")
    add_fees: Optional[float]       = Field(description="Additional fees (in dollars).")
    rpt_limit: Optional[int]        = Field(description="Repeat limit. There may be other repeat limits not listed here you should keep in mind.")
    notes: Optional[str]            = Field(description="Notes for a section.")


class SectionDB(SectionBase, table=True):
    year: int                       = Field(primary_key=True)
    term: int                       = Field(primary_key=True)
    
    schedule: list[ScheduleEntry]   = Relationship()


class SectionAPI(SectionBase):
    schedule:list[ScheduleEntry]    = []