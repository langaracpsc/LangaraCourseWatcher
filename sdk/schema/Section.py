from enum import Enum
from typing import List, Optional, Union, TYPE_CHECKING
from sqlmodel import Field, Relationship, SQLModel

from sdk.schema.ScheduleEntry import ScheduleEntryAPI


# from sdk.schema.ScheduleEntry import ScheduleEntryDB

if TYPE_CHECKING:
    from sdk.schema.ScheduleEntry import ScheduleEntryDB
    from sdk.schema_built.Course import CourseAPIBuild

    

class RPEnum(Enum):
    R = "R"
    P = "P"
    RP = "RP"

class SectionBase(SQLModel):    
    crn: int                        = Field(index=True, description="Always 5 digits long.")
    
    RP : Optional["RPEnum"]           = Field(default=None, description='Prerequisites of the course.')
    seats: Optional[str]            = Field(default=None, description='```"Inact"``` means registration isn\'t open yet. \n\n```"Cancel"``` means that the course is cancelled.')
    waitlist: Optional[str]         = Field(default=None, description='```null``` means that the course has no waitlist (ie MATH 1183 & MATH 1283). \n\n```"N/A"``` means the course does not have a waitlist.')
    subject: str                    = Field(default=None, index=True, description="Subject area e.g. ```CPSC```.")
    course_code: int                = Field(default=None, index=True,  description="Course code e.g. ```1050```.")
    section: Optional[str]          = Field(default=None, description="Section e.g. ```001```, ```W01```, ```M01```.")
    credits: float                  = Field(default=0, description="Credits the course is worth.")
    abbreviated_title: Optional[str]= Field(default=None, description="Abbreviated title of the course e.g. ```Algrthms & Data Strctrs I```.")
    add_fees: Optional[float]       = Field(default=None, description="Additional fees (in dollars).")
    rpt_limit: Optional[int]        = Field(default=0, description="Repeat limit. There may be other repeat limits not listed here you should keep in mind.")
    notes: Optional[str]            = Field(default=None, description="Notes for a section.")


class SectionDB(SectionBase, table=True):
    id:str                          = Field(primary_key=True, description="Unique identifier for a section.")
    year: int                       = Field(index=True)
    term: int                       = Field(index=True)
    
    schedule: List["ScheduleEntryDB"]   = Relationship(back_populates="section")


class SectionAPI(SectionBase):
    schedule: List["ScheduleEntryAPI"] = []
    id: str = Field()
    
    # course_id: Optional[str] = Field(default=None, foreign_key="sectiondb.id")
    # course: Optional["CourseAPIExt"] = Relationship(back_populates="schedule")