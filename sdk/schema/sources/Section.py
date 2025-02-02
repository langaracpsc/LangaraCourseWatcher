from enum import Enum
from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Field, Relationship, SQLModel

from sdk.schema.sources.ScheduleEntry import ScheduleEntryAPI, ScheduleEntryDB

if TYPE_CHECKING:
    from sdk.schema.aggregated.Course import (
        CourseDB,
    )  # This import won't cause runtime issues


class RPEnum(Enum):
    R = "R"
    P = "P"
    RP = "RP"


class SectionBase(SQLModel):
    id: str = Field(
        primary_key=True,
        description="Internal primary and unique key (e.g. SECT-ENGL-1123-2024-30-31005).",
    )

    crn: int = Field(index=True, description="Always 5 digits long.")
    RP: Optional["RPEnum"] = Field(
        default=None, description="Prerequisites of the course."
    )
    seats: Optional[str] = Field(
        default=None,
        description='```"Inact"``` means registration isn\'t open yet. \n\n```"Cancel"``` means that the course is cancelled.',
    )
    waitlist: Optional[str] = Field(
        default=None,
        description='```null``` means that the course has no waitlist (ie MATH 1183 & MATH 1283). \n\n```"N/A"``` means the course does not have a waitlist.',
    )
    # subject: str                    = Field(default=None, index=True, description="Subject area e.g. ```CPSC```.")
    # course_code: str                = Field(default=None, index=True,  description="Course code e.g. ```1050```.")
    section: Optional[str] = Field(
        default=None, description="Section e.g. ```001```, ```W01```, ```M01```."
    )
    credits: float = Field(default=0, description="Credits the course is worth.")
    abbreviated_title: Optional[str] = Field(
        default=None,
        description="Abbreviated title of the course e.g. ```Algrthms & Data Strctrs I```.",
    )
    add_fees: Optional[float] = Field(
        default=None, description="Additional fees (in dollars)."
    )
    rpt_limit: Optional[int] = Field(
        default=0,
        description="Repeat limit. There may be other repeat limits not listed here you should keep in mind.",
    )
    notes: Optional[str] = Field(default=None, description="Notes for a section.")


class SectionDB(SectionBase, table=True):
    subject: str = Field(index=True, foreign_key="coursedb.subject")
    course_code: str = Field(index=True, foreign_key="coursedb.course_code")
    year: int = Field(index=True, foreign_key="semester.year")
    term: int = Field(index=True, foreign_key="semester.term")

    id_semester: str = Field(index=True, foreign_key="semester.id")

    id_course: str = Field(index=True, foreign_key="coursedb.id")
    # course: "CourseDB" = Relationship(back_populates="sections")

    course: "CourseDB" = Relationship(
        back_populates="sections",
        sa_relationship_kwargs={
            "primaryjoin": "SectionDB.id_course==CourseDB.id",
            "viewonly": True,
        },
    )

    schedule: List["ScheduleEntryDB"] = Relationship(
        back_populates="section",
        sa_relationship_kwargs={"lazy": "selectin", "viewonly": True},
    )


class SectionAPI(SectionBase):
    subject: str
    course_code: str
    year: int
    term: int

    schedule: List["ScheduleEntryAPI"] = []

    class Config:
        json_schema_extra = {
            "example": {
                "id": "SECT-ENGL-1123-2024-10-10924",
                "crn": 10924,
                "RP": "P",
                "seats": "4",
                "waitlist": None,
                "section": "001",
                "credits": 3.0,
                "abbreviated_title": "Intro to Academic Writing",
                "add_fees": None,
                "rpt_limit": 2,
                "notes": None,
                "subject": "ENGL",
                "course_code": "1123",
                "year": 2024,
                "term": 10,
                "schedule": [
                    # ScheduleEntryAPI.Config.json_schema_extra["example"]
                ],
            }
        }

    # course_id: Optional[str] = Field(default=None, foreign_key="sectiondb.id")
    # course: Optional["CourseAPIExt"] = Relationship(back_populates="schedule")


class SectionAPIList(SQLModel):
    sections: list[SectionAPI]
