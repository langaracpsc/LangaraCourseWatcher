from sqlmodel import Field, Relationship, SQLModel

from sdk.schema.BaseModels import Course

"""
Stores the attributes of all courses
Data is also available by term so we store that as well

Source: https://langara.ca/programs-and-courses/courses/course-attributes.html
"""
class CourseAttribute(SQLModel):
    attr_ar: bool   = Field(default=False, description="Meets second-year arts requirement (2AR).")
    attr_sc: bool   = Field(default=False, description="Meets second-year science requirement (2SC).")
    attr_hum: bool  = Field(default=False, description="Meets humanities requirement (HUM).")
    attr_lsc: bool  = Field(default=False, description="Meets lab-science requirement (LSC).")
    attr_sci: bool  = Field(default=False, description="Meets science requirement (SCI).")
    attr_soc: bool  = Field(default=False, description="Meets social science requirement (SOC).")
    attr_ut: bool   = Field(default=False, description='Meets "university-transferable" requirements. Course transfers to at least one of UBC, UBCO, SFU, UVIC, and UNBC (UT).')
    

class CourseAttributeDB(CourseAttribute, table=True):
    id: str     = Field(primary_key=True, description="Internal primary and unique key (e.g. ATRB-ENGL-1123-2024-30).")
    
    # 1:many relationship with course    
    subject: str        = Field(index=True, foreign_key="course.subject")
    course_code: int    = Field(index=True, foreign_key="course.course_code")
    year: int           = Field(index=True, foreign_key="semester.year")
    term: int           = Field(index=True, foreign_key="semester.term")
    
    # id_course: str      = Field(index=True, foreign_key="course.id")
    # id_semester: str    = Field(index=True, foreign_key="semester.id")
    
    course: Course = Relationship(
        sa_relationship_kwargs={"primaryjoin": "CourseAttributeDB.subject==Course.subject and CourseAttributeDB.course_code==Course.course_code", "lazy": "joined"}
    )
    
    