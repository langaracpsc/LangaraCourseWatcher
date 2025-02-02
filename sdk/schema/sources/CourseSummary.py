from typing import Optional

from sqlmodel import Field, Relationship, SQLModel

from sdk.schema.aggregated.Course import CourseDB

"""
Stores information taken from the course catalogue
Frankly I'm not sure if this page is even supposed to be public
Data is also available by semester
But pages before 2011 are in a different format

Source: https://swing.langara.bc.ca/prod/hzgkcald.P_DisplayCatalog
"""


class CourseSummary(SQLModel):
    title: str = Field(
        index=True,
        description="*Unabbreviated* title of the course e.g. ```Intro to Computer Science```.",
    )

    desc_replacement_course: Optional[str] = Field(
        description="If this course is discontinued / what it was replaced by."
    )
    description: Optional[str] = Field(description="Description of course.")
    desc_last_updated: Optional[str] = Field(
        description="Taken from old catalogues. Not a trustworthy number as the dates are locked in the past."
    )
    desc_requisites: Optional[str] = Field(description="gah.")

    credits: float = Field(description="Credits of the course.")
    hours_lecture: float = Field(
        default=False, description="Lecture hours of the course."
    )
    hours_seminar: float = Field(
        default=False, description="Seminar hours of the course."
    )
    hours_lab: float = Field(default=False, description="Lab hours of the course.")


class CourseSummaryDB(CourseSummary, table=True):
    id: str = Field(
        primary_key=True,
        description="Internal primary and unique key (e.g. `CSMR-ENGL-1123-2024-30`).",
    )

    # 1:many relationship with course
    subject: str = Field(index=True, foreign_key="coursedb.subject")
    course_code: str = Field(index=True, foreign_key="coursedb.course_code")
    year: int = Field(index=True, foreign_key="semester.year")
    term: int = Field(index=True, foreign_key="semester.term")

    # course: CourseDB = Relationship(
    #     sa_relationship_kwargs={"primaryjoin": "CourseSummaryDB.subject==Course.subject and CourseSummaryDB.course_code==Course.course_code"}
    # )
