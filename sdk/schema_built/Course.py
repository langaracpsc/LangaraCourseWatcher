from enum import Enum

from typing import Optional
from sqlmodel import Field, SQLModel, Relationship

from sdk.schema.Section import RPEnum, SectionAPI, SectionDB
from sdk.schema.Transfer import Transfer, TransferAPI, TransferDB



class availabilitiesEnum(Enum):
    spring =        "Spring"
    summer =        "Summer"
    fall =          "Fall"
    springsummer =  "Spring & Summer"
    springfall =    "Spring & Fall"
    summerfall =    "Summer & Fall"
    all =           "All Semesters"
    unknown =       "Unknown"
    discontinued =  "Discontinued"
    
class PrereqEnum(Enum):
    ALL_OF = "ALL OF"
    ONE_OF = "ONE OF"
    COREQ = "COREQ"
    REQ = "REQ"

# probably needs its own class once implemented
class Prerequisite(SQLModel):
    type : PrereqEnum
    course : str
    grade : Optional[str]

    
# TODO: fill in all attributes from all possible sources




class CourseBase(SQLModel):
    id:str = Field(primary_key=True, description="Unique identifier for each Course.")
    
    # GENERAL INFO
    subject: str        = Field(description="Subject area e.g. ```CPSC```.")
    course_code: int    = Field(description="Course code e.g. ```1050```.")
    
    # FROM CourseSummary.py
    credits: float              = Field(default=-1, description="Credits the course is worth.")
    
    title: str                  = Field(default="", description="*Unabbreviated* title of the course e.g. ```Intro to Computer Science```.")
    description: Optional[str]  = Field(default=None, description="Description of course.")
    
    hours_lecture: float          = Field(default=0, description="Lecture hours of the course.")
    hours_seminar: float          = Field(default=0, description="Lecture hours of the course.")
    hours_lab: float              = Field(default=0, description="Lecture hours of the course.")
    
    # TODO: Not implemented (needs another scraper ._.)
    # course_outline_url: Optional[str] = Field(default=None, description="Link to course outline (if available).")
    
    # Generated from Section.py (uses the most recent section)
    RP : Optional[RPEnum]           = Field(default=None, description='Prerequisites of the course.')
    abbreviated_title: Optional[str]    = Field(default=None, description="Abbreviated title of the course e.g. ```Algrthms & Data Strctrs I```.")
    add_fees: Optional[float]           = Field(default=0, description="Additional fees (in dollars).")
    rpt_limit: Optional[int]            = Field(default=0, description="Repeat limit. There may be other repeat limits not listed here you should keep in mind.")

    # FROM Attribute.py
    attr_ar: bool   =Field(default=False, description="Second year arts course.")
    attr_sc: bool   =Field(default=False, description="Second year science course.")
    attr_hum: bool  =Field(default=False, description="Humanities course.")
    attr_lsc: bool  =Field(default=False, description="Lab science course.")
    attr_sci: bool  =Field(default=False, description="Science course.")
    attr_soc: bool  =Field(default=False, description="SOC course.")
    attr_ut: bool   =Field(default=False, description="University transferrable course.")
    
    # Derived from Section.py (uses aggregate data from all sections)
    # average_seats: Optional[float]        = Field(default=None)
    # average_waitlist: Optional[float]     = Field(default=None)
    # maximum_seats: Optional[int]          = Field(default=None)

    last_offered_year: Optional[int] = Field(default=None, description="The last year the course was offered e.g. ```2023```.")
    last_offered_term: Optional[int]  = Field(default=None, description="The last term the course was offered e.g. ```10```.")
    first_offered_year: Optional[int] = Field(default=None, description="The first year the course was offered e.g. ```2013```.")
    first_offered_term: Optional[int]    = Field(default=None, description="The first term the course was offered e.g. ```30```.")
    
    # Derived from multiple sources
    # availability: availabilitiesEnum            = Field(default=None, description="(NOT IMPLEMENTED) Availability of course. Extracted automatically - may not be correct. Consult Langara advisors if in doubt.")
    # prerequisites: Optional[list[Prerequisite]] = Field(default=[], description="(NOT IMPLEMENTED) Prerequisites for the course.")
    
    # restriction: Optional[str]                  = Field(default=None, description="(NOT IMPLEMENTED) Program you must be in to register for this course.")
    
    # THE MOST IMPORTANT PART

class CourseDB(CourseBase, table=True):
    id:str = Field(primary_key=True, description="Unique identifier for each Course.")
    
    # this only changes when we run the course search, so we should
    # prefill the data instead of running a query live
    latest_course_summary_id: Optional[str] = Field(foreign_key="coursesummarydb.id")
    latest_section_id: Optional[str]        = Field(foreign_key="sectiondb.id")
    latest_attribute_id: Optional[str]      = Field(foreign_key="attributedb.id")
    
    

class CourseAPIBuild(CourseBase):
    
    # all of these will be removed once the course is returned
    year: int = Field(default=0)
    term: int = Field(default=0)
    
    
    offerings: list[SectionAPI]                 = Field(default=[], description="All past offerings of the course")
    transfers: list[TransferDB]                   = Field(default=[], description="Information on how the course transfers.")

class CourseAPIExt(CourseBase):
    offerings: list[SectionAPI]                 = Field(default=[], description="All past offerings of the course")
    transfers: list[TransferAPI]                   = Field(default=[], description="Information on how the course transfers.")

class CourseAPI(CourseBase):
    # offerings: list[SectionAPI]                 = Field(default=[], description="All past offerings of the course")
    transfers: list[TransferAPI]                   = Field(default=[], description="Information on how the course transfers.")



    # class Config:
    #     json_schema_extra = {
    #         "example": {
    #             "RP" : None,
    #             "subject" : "CPSC",
    #             "course_code" : 1050,
    #             "credits" : 3.0,
    #             "title": "Introduction to Computer Science",
    #             "description" : "Offers a broad overview of the computer science discipline.  Provides students with an appreciation for and an understanding of the many different aspects of the discipline.  Topics include information and data representation; introduction to computer hardware and programming; networks; applications (e.g., spreadsheet, database); social networking; ethics; and history.  Intended for both students expecting to continue in computer science as well as for those taking it for general interest.",
    #             "hours": {
    #                 "lecture": 4,
    #                 "seminar": 0,
    #                 "lab": 2
    #             },
    #             "add_fees" : 34.,
    #             "rpt_limit" : 2,
    #             # TODO: fix attributes
    #             # "attributes" : {
    #             #     "2AR" : False,
    #             #     "2SC" : False,
    #             #     "HUM" : False,
    #             #     "LSC" : False,
    #             #     "SCI" : True,
    #             #     "SOC" : False,
    #             #     "UT" :  True,
    #             # },
    #             "transfer" : [
    #                 Transfer.Config.json_schema_extra["example1"],
    #                 Transfer.Config.json_schema_extra["example2"]
    #                 ],
    #         }
    #     }
        