from typing import Optional
from sqlmodel import Field, Relationship, SQLModel

from sdk.schema.BaseModels import Course

"""
All the data contained in the course page on the langara website
(except for the course outlines which get their own table)

Source: https://langara.ca/programs-and-courses/courses/ENGL/1123.html
"""
class CoursePage(SQLModel):
    title: str                  = Field(description="*Unabbreviated* title of the course e.g. ```Intro to Computer Science```.")
    description: Optional[str]  = Field(description="Description of course.")
    
    credits: float              = Field(description="Credits of the course.")
    hours_lecture: float        = Field(description="Lecture hours of the course.")
    hours_seminar: float        = Field(description="Seminar hours of the course.")
    hours_lab: float            = Field(description="Lab hours of the course.")
    
    desc_replacement_course: Optional[str]             = Field(description="If this course is discontinued / what it was replaced by.")
    description: Optional[str]                   = Field(description="Summary of the course.")
    desc_duplicate_credit: Optional[str]         = Field(description="If the credits for this course exclude credits from another course.")
    desc_registration_restriction: Optional[str] = Field(description="If a course is restricted or has priority registration it will say here.")
    desc_prerequisite: Optional[str]             = Field(description="Prerequisites of the course are stated here.")

    university_transferrable: bool  = Field(description="If the course is university transferrable.")
    offered_online: bool            = Field(description="If there are online offerings for the course.")
    preparatory_course: bool        = Field(description="If the course is prepatory (ie does not offer credits.)")


class CoursePageDB(CoursePage, table=True):
    id: str     = Field(primary_key=True, description="Internal primary and unique key (e.g. CPGE-ENGL-1123).")
    # 1:1 relationship with course
    subject: str        = Field(index=True, foreign_key="course.subject")
    course_code: int    = Field(index=True, foreign_key="course.course_code")
    
    id_course: str      = Field(index=True, foreign_key="course.id")
    
    course: Course = Relationship(
        sa_relationship_kwargs={"primaryjoin": "CoursePageDB.subject==Course.subject", "lazy": "joined"}
    )