import logging

from enum import Enum
from typing import Optional
from sqlmodel import Field, SQLModel

from sdk.schema.Section import SectionAPI, SectionDB
from sdk.schema.ScheduleEntry import ScheduleEntryDB
from sdk.schema.Attribute import AttributeDB
from sdk.schema.CourseSummary import CourseSummaryDB

from sdk.schema_built.Course import CourseAPI

class Semesters(Enum):
    spring = 10
    summer = 20
    fall = 30


class Semester(SQLModel):
    year: int               = Field(description='Year of semester e.g. ```2024```.')
    term: int               = Field(description='Term of semester e.g. ```30```.')
    
    
class SemesterCourses(Semester):
    courses: list[CourseAPI] = Field(default=[])
    
class SemesterSections(Semester):
    sections: list[SectionAPI] = Field(default=[])
    
    # attributes: list[AttributeDB]           = Field(default=[])
    # courseSummaries: list[CourseSummaryDB]  = Field(default=[])
    # sections: list[SectionDB]               = Field(default=[], description='List of sections in the semester.')
    # schedules: list[ScheduleEntryDB]        = Field(default=[])
    
        
    # class Config:
    #     json_schema_extra = {
    #         "example": {
    #             # "datetime_retrieved" : "2023-04-04",
    #             "year": 2023,
    #             "term" : Semesters.spring,
    #             # "courses_first_day" : "2023-5-08",
    #             # "courses_last_day" : "2023-8-31",
    #             # "courses" : [CourseEnhanced.Config.json_schema_extra[0]]
    #         }
    #     }
    