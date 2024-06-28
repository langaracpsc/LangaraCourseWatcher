from sqlmodel import Field, Relationship, SQLModel

from sdk.schema.BaseModels import Course

"""
The course outlines which are available on the Langara course pages

Source: https://langara.ca/programs-and-courses/courses/ENGL/1123.html
"""
class CourseOutline(SQLModel):
    url: str       = Field(description="URL to the pdf of the course outline.")
    file_name: str   = Field(description="Text that links to the course outline e.g. `CPSC 1150 - Summer 2021 (v. 1)`.")
    
class CourseOutlineDB(CourseOutline, table=True):
    id: str     = Field(primary_key=True, description="Internal primary and unique key (e.g. OUTL-ENGL-1123-1).")
    
    # 1:many relationship with course
    subject: str        = Field(index=True, foreign_key="course.subject")
    course_code: str    = Field(index=True, foreign_key="course.course_code")
    
    id_course: str      = Field(index=True, foreign_key="course.id")
    id_course_max : str = Field(index=True, foreign_key="coursemaxdb.id")
    
    course: Course = Relationship(
        sa_relationship_kwargs={"primaryjoin": "CourseOutlineDB.id_course==Course.id", "lazy": "joined"}
    )

class CourseOutlineAPI(CourseOutline):
    id: str
    