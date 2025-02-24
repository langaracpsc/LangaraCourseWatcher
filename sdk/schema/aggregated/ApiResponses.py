from requests_cache import Optional
from sqlmodel import Field, SQLModel

from sdk.schema.aggregated.Course import CourseAPI, CourseAPILight
from sdk.schema.aggregated.Semester import Semester
from sdk.schema.aggregated.CourseMax import CourseMaxAPI
from sdk.schema.sources.Section import SectionDB


class IndexSemesterList(SQLModel):
    count: int
    semesters: list[Semester]
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "count": 2, 
                    "semesters" : [
                        Semester.Config.json_schema_extra["examples"][0],
                        Semester.Config.json_schema_extra["examples"][1]
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
                    "count": 87, 
                    "subjects" : [
                        "ABST",
                        "AHIS",
                        "ANTH",
                        "APPL",
                        "APSC",
                        "ASIA",
                        "ASTR",
                        "BCAP",
                        "BFIN",
                        "BINF",
                        "BIOL",
                        "BUSM",
                        "CCAP",
                        "CHEM",
                        "CHIN",
                        "CISY",
                        "CJUS",
                        "CLST",
                        "CMNS",
                        "CNST",
                        "COOP",
                        "CPSC",
                        "CREV",
                        "CRIM",
                        "CSIS",
                        "DANA",
                        "DASH",
                        "DDSN",
                        "DSGN",
                        "ECED",
                        "ECON",
                        "EDAS",
                        "ENGL",
                        "ENVS",
                        "EURO",
                        "EXCH",
                        "EXPE",
                        "FINA",
                        "FLMA",
                        "FMGT",
                        "FMST",
                        "FREN",
                        "FSRV",
                        "GEOG",
                        "GEOL",
                        "GERO",
                        "GREK",
                        "HCAS",
                        "HIST",
                        "HKIN",
                        "HMPF",
                        "HSCI",
                        "INST",
                        "INTB",
                        "JAPN",
                        "JOUR",
                        "KINS",
                        "LAMS",
                        "LATN",
                        "LIBR",
                        "MARK",
                        "MATH",
                        "NURS",
                        "NUTR",
                        "PACR",
                        "PCCN",
                        "PHED",
                        "PHIL",
                        "PHOT",
                        "PHYS",
                        "POLI",
                        "PSYC",
                        "PUBL",
                        "RECR",
                        "RELS",
                        "REST",
                        "SBUS",
                        "SCIE",
                        "SOCI",
                        "SPAN",
                        "SPED",
                        "SSRV",
                        "STAT",
                        "THEA",
                        "WILX",
                        "WMDD",
                        "WMST"
                        ]
                }
            ]
        }
    }

class IndexCourse(SQLModel):
    subject: str
    course_code: str
    title: Optional[str]
    on_langara_website: bool
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "subject" : "ENGL", 
                    "course_code" : "1100",
                    "title" : "Reading and Writing about Literature",
                    "on_langara_website" : True
                },
                {
                    "subject" : "ENGL", 
                    "course_code" : "1106",
                    "title" : "ACCESS Langara I",
                    "on_langara_website" : True
                }
            ]
        }
    }
                
    
class IndexTransfer(SQLModel):
    code: str
    name: str
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "code" : "UBCV", 
                    "name" : "University of British Columbia - Vancouver",
                },
                {
                    "code" : "SFU", 
                    "name" : "Simon Fraser University",
                }
            ]
        }
    }

class IndexCourseList(SQLModel):
    subject_count: int
    course_count: int
    courses: list[IndexCourse]
    
    # subjects: dict[str, list[int]]
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "subject_count": 1,
                    "course_count": 2,
                    "courses": [
                        IndexCourse.model_config["json_schema_extra"]["examples"][0],
                        IndexCourse.model_config["json_schema_extra"]["examples"][1]
                    ]
                }
            ]
        }
    
class SearchCourse(SQLModel):
    subject: str
    course_code: str
    on_langara_website: bool
    
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
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "data": {
                    "last_updated": "2024-10-30T12:00:00Z",
                    "db_version": "2"
                }
            }
        }
    }
        
class ExportCourseList(SQLModel):
    courses: list[CourseAPILight]
    
class IndexTransferList(SQLModel):
    transfers: list[IndexTransfer]
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "transfers": [
                        IndexTransfer.model_config["json_schema_extra"]["examples"][0],
                        IndexTransfer.model_config["json_schema_extra"]["examples"][1]
                    ]
                }
            ]
        }
    
class ExportSectionList(SQLModel):
    sections: list[SectionDB]