from requests_cache import Optional
from sqlmodel import Field, SQLModel

from sdk.schema.aggregated.Course import CourseAPI, CourseAPILight
from sdk.schema.aggregated.Semester import Semester
from sdk.schema.aggregated.CourseMax import CourseMaxAPI


class IndexSemesterList(SQLModel):
    count: int
    semesters: list[Semester]
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "count": 75, 
                    "semesters" : [
                        {
                            "year": 2023, 
                            "term": 20
                        }
                    ]
                }
            ]
        }
    }

class IndexSubjectList(SQLModel):
    count: int
    subjects: list[str]
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "count": 80, 
                    "subjects" : ["ABST", "AHIS"]
                }
            ]
        }
    }

class IndexCourse(SQLModel):
    subject: str
    course_code: str
    title: Optional[str]
    active: bool
    
class IndexTransfer(SQLModel):
    code: str
    name: str
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "code" : "UBCV", 
                    "name" : "University of British Columbia - Vancouver",
                }
            ]
        }
    }

class IndexCourseList(SQLModel):
    subject_count: int
    course_count: int
    courses: list[IndexCourse]
    
    # subjects: dict[str, list[int]]
    
    # model_config = {
    #     "json_schema_extra": {
    #         "examples": [
    #             {
    #                 "subject_count" : 80, 
    #                 "course_count" : 1500,
    #                 "subjects" : {"ENGL" : [1100, 1101]}
    #             }
    #         ]
    #     }
    # }

class SearchCourse(SQLModel):
    subject: str
    course_code: str
    active: bool
    
class SearchCourseList(SQLModel):
    subject_count: int
    course_count: int
    courses: list[SearchCourse]


class SearchSectionList(SQLModel):
    subject_count: int
    course_count: int
    section_count: int
    sections: list[str]

class PaginationPage(SQLModel):
    page: int
    courses_per_page: int
    total_courses: int
    total_pages: int
    courses: list[CourseAPI]
    
class MetadataFormatted(SQLModel):
    data: dict
    
    
    class Config:
        json_schema_extra = {
            "example": {
                "data": {
                    "last_updated": "2024-10-30T12:00:00Z",
                    "db_version": "2"
                }
            }
        }
        
class ExportCourseList(SQLModel):
    courses: list[CourseAPILight]
    
class IndexTransferList(SQLModel):
    transfers: list[IndexTransfer]