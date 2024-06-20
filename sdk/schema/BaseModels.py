from requests_cache import Optional
from sqlmodel import Field, Relationship, SQLModel

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sdk.schema.CourseAttribute import CourseAttributeDB
    from sdk.schema.CourseOutline import CourseOutlineDB
    from sdk.schema.CoursePage import CoursePage
    from sdk.schema.CourseSummary import CourseSummaryDB
    from sdk.schema.Section import SectionDB
    from sdk.schema.Transfer import TransferDB


class Course(SQLModel, table=True):
    id: str             = Field(primary_key=True, description="Internal primary key (e.g. CRSE-ENGL-1123).")
    subject: str        = Field(description="Subject area e.g. ```CPSC```.")
    course_code: int    = Field(description="Course code e.g. ```1050```.")
    
    # attributes: list["CourseAttributeDB"] = Relationship(back_populates="course")
    # outlines: list["CourseOutlineDB"] = Relationship(back_populates="course")
    # page: "CoursePage" = Relationship(back_populates="course")
    # summaries: list["CourseSummaryDB"] = Relationship(back_populates="course")
    # sections: list["SectionDB"] = Relationship(back_populates="course")
    
    # transfers: list["TransferDB"] = Relationship(back_populates="course")

class Semester(SQLModel, table=True):
    id: str     = Field(primary_key=True, description="Internal primary key (e.g. SMTR-2024-30).")
    
    year: int   = Field(description='Year e.g. ```2024```.')
    term: int   = Field(description='Term e.g. ```30```')
    
    courses_first_day: Optional[str] = Field(default=None, description="First day of normal classes.")
    courses_last_day: Optional[str] = Field(default=None, description="Last day of normal classes.")
    
    # sections: list["SectionDB"] = Relationship()