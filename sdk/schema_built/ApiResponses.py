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


class IndexCourseList(SQLModel):
    subject_count: int
    course_code_count: int
    subjects: dict[str, list[int]]
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "subject_count" : 80, 
                    "course_code_count" : 1500,
                    "subjects" : {"ENGL" : [1100, 1101]}
                }
            ]
        }
    }
    