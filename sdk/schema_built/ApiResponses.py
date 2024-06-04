from sqlmodel import SQLModel


class IndexSemester(SQLModel):
    year:int
    term:int
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "year": 2023, 
                    "term": 20
                }
            ]
        }
    }

class IndexSemesterList(SQLModel):
    count: int
    semesters: list[IndexSemester]
    
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
    course_code: int
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "subject": "ENGL", 
                    "course_code": 1123
                }
            ]
        }
    }

class IndexCourseList(SQLModel):
    count: int
    courses: list[IndexCourse]
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "count": 1500, 
                    "courses" : [
                        {
                            "subject": "ENGL", 
                            "course_code": 1123
                        }
                    ]
                }
            ]
        }
    }
    