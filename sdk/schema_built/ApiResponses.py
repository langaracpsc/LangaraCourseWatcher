from requests_cache import Optional
from sqlmodel import SQLModel

from sdk.schema.BaseModels import Semester
from sdk.schema_built.CourseMax import CourseMaxAPI


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

class IndexCourseList(SQLModel):
    subject_count: int
    course_code_count: int
    courses: list[IndexCourse]
    
    # subjects: dict[str, list[int]]
    
    # model_config = {
    #     "json_schema_extra": {
    #         "examples": [
    #             {
    #                 "subject_count" : 80, 
    #                 "course_code_count" : 1500,
    #                 "subjects" : {"ENGL" : [1100, 1101]}
    #             }
    #         ]
    #     }
    # }
    
class PaginationPage(SQLModel):
    page: int
    courses_per_page: int
    total_courses: int
    total_pages: int
    courses: list[CourseMaxAPI]