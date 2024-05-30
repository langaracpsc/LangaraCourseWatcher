from enum import Enum

from typing import Optional
from sqlmodel import Field, SQLModel

from sdk.schema.Section import RPEnum, SectionAPI, SectionDB
from sdk.schema.Transfer import Transfer



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

class CourseAPI(SQLModel):
    
    # GENERAL INFO
    year: int                       = Field(primary_key=True, description='Year e.g. ```2024```.')
    term: int                       = Field(primary_key=True, description='Term e.g. ```30```')
    subject: str        = Field(description="Subject area e.g. ```CPSC```.")
    course_code: int    = Field(description="Course code e.g. ```1050```.")
    
    # FROM Attribute.py
    attr_ar: bool   =Field(default=False, description="Second year arts course.")
    attr_sc: bool   =Field(default=False, description="Second year science course.")
    attr_hum: bool  =Field(default=False, description="Humanities course.")
    attr_lsc: bool  =Field(default=False, description="Lab science course.")
    attr_sci: bool  =Field(default=False, description="Science course.")
    attr_soc: bool  =Field(default=False, description="SOC course.")
    attr_ut: bool   =Field(default=False, description="University transferrable course.")
    
    # FROM CourseSummary.py
    credits: float              = Field(description="Credits the course is worth.")
    
    title: str                  = Field(description="*Unabbreviated* title of the course e.g. ```Intro to Computer Science```.")
    description: Optional[str]  = Field(description="Description of course.")
    
    hours_lecture: int          = Field(default=False, description="Lecture hours of the course.")
    hours_seminar: int          = Field(default=False, description="Lecture hours of the course.")
    hours_lab: int              = Field(default=False, description="Lecture hours of the course.")
    
    # TODO: Not implemented (needs another scraper ._.)
    course_outline_url: Optional[str] = Field(description="Link to course outline (if available).")
    
    # Generated from Section.py (uses the most recent section)
    RP : Optional[RPEnum]           = Field(description='Prerequisites of the course.')
   
    abbreviated_title: Optional[str]    = Field(description="Abbreviated title of the course e.g. ```Algrthms & Data Strctrs I```.")
    add_fees: Optional[float]           = Field(description="Additional fees (in dollars).")
    rpt_limit: Optional[int]            = Field(description="Repeat limit. There may be other repeat limits not listed here you should keep in mind.")

    # Derived from Section.py (uses aggregate data from all sections)
    average_seats: float
    average_waitlist: float
    maximum_seats: int 


    # Derived from multiple sources
    availability: availabilitiesEnum            = Field(description="Availability of course. Extracted automatically - may not be correct. Consult Langara advisors if in doubt.")
    prerequisites: Optional[list[Prerequisite]] = Field(description="Prerequisites for the course. (NOT IMPLEMENTED)")
    
    restriction: None                           = Field(description="Program you must be in to register for this course. (NOT IMPLEMENTED)")
    
    # THE MOST IMPORTANT PART
    transfers: list[Transfer]                   = Field(description="Information on how the course transfers.")
    # offerings: list[SectionAPI]                  = Field(description="All past offerings of the course")
        



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
        