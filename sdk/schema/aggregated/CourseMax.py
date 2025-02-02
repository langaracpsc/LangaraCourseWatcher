from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy.orm import RelationshipProperty
from sqlmodel import Field, Relationship, SQLModel

from sdk.schema.sources.CourseOutline import (
    CourseOutline,
    CourseOutlineAPI,
    CourseOutlineDB,
)
from sdk.schema.sources.Section import RPEnum, SectionAPI
from sdk.schema.sources.Transfer import Transfer, TransferAPI, TransferDB

if TYPE_CHECKING:
    from sdk.schema.aggregated.Course import CourseDB


class availabilitiesEnum(Enum):
    spring = "Spring"
    summer = "Summer"
    fall = "Fall"
    springsummer = "Spring & Summer"
    springfall = "Spring & Fall"
    summerfall = "Summer & Fall"
    all = "All Semesters"
    unknown = "Unknown"
    not_offered = "Not Offered"
    discontinued = "Discontinued"


# TODO: fill in all attributes from all possible sources


class CourseMax(SQLModel):
    # FROM CourseSummary.py
    credits: Optional[float] = Field(
        default=None, description="Credits that the course is worth."
    )

    title: Optional[str] = Field(
        default=None,
        description="*Unabbreviated* title of the course e.g. ```Intro to Computer Science```.",
    )

    # FROM CoursePage.py
    desc_replacement_course: Optional[str] = Field(
        description="If this course is discontinued / what it was replaced by."
    )
    description: Optional[str] = Field(description="Summary of the course.")
    desc_duplicate_credit: Optional[str] = Field(
        description="If the credits for this course exclude credits from another course."
    )
    desc_registration_restriction: Optional[str] = Field(
        description="If a course is restricted or has priority registration it will say here."
    )
    desc_prerequisite: Optional[str] = Field(
        description="Prerequisites of the course are stated here."
    )

    hours_lecture: Optional[float] = Field(
        default=None, description="Lecture hours of the course."
    )
    hours_seminar: Optional[float] = Field(
        default=None, description="Lecture hours of the course."
    )
    hours_lab: Optional[float] = Field(
        default=None, description="Lecture hours of the course."
    )

    # university_transferrable: Optional[bool]  = Field(description="If the course is university transferrable.")
    offered_online: Optional[bool] = Field(
        default=None, description="If there are online offerings for the course."
    )
    preparatory_course: Optional[bool] = Field(
        default=None,
        description="If the course is prepatory (ie does not offer credits.)",
    )

    # FROM Section.py (uses the most recent section)
    RP: Optional[RPEnum] = Field(
        default=None, description="Prerequisites of the course."
    )
    abbreviated_title: Optional[str] = Field(
        default=None,
        description="Abbreviated title of the course e.g. ```Algrthms & Data Strctrs I```.",
    )
    add_fees: Optional[float] = Field(
        default=None, description="Additional fees (in dollars)."
    )
    rpt_limit: Optional[int] = Field(
        default=None,
        description="Repeat limit. There may be other repeat limits not listed here you should keep in mind.",
    )

    # FROM Attribute.py
    attr_ar: Optional[bool] = Field(
        default=None, description="Second year arts course."
    )
    attr_sc: Optional[bool] = Field(
        default=None, description="Second year science course."
    )
    attr_hum: Optional[bool] = Field(default=None, description="Humanities course.")
    attr_lsc: Optional[bool] = Field(default=None, description="Lab science course.")
    attr_sci: Optional[bool] = Field(default=None, description="Science course.")
    attr_soc: Optional[bool] = Field(default=None, description="SOC course.")
    attr_ut: Optional[bool] = Field(
        default=None, description="University transferrable course."
    )

    # Calculated from Section
    first_offered_year: Optional[int] = Field(
        default=None,
        description="The first year the course was offered e.g. ```2013```.",
    )
    first_offered_term: Optional[int] = Field(
        default=None, description="The first term the course was offered e.g. ```30```."
    )
    last_offered_year: Optional[int] = Field(
        default=None,
        description="The last year the course was offered e.g. ```2023```.",
    )
    last_offered_term: Optional[int] = Field(
        default=None, description="The last term the course was offered e.g. ```10```."
    )

    # Derived from multiple sources
    # NOT IMPLEMENTED BECAUSE IT SEEMS LIKE A VALUE JUDGEMENT
    # availability: Optional[availabilitiesEnum] = Field(default=None, description="(NOT IMPLEMENTED) Availability of course. Extracted automatically - may not be correct. Consult Langara advisors if in doubt.")
    on_langara_website: Optional[bool] = Field(
        default=None,
        description="Whether a page for this course is active on the Langara website. This is not a guarantee that a course is being actively offered.",
    )
    discontinued: Optional[bool] = Field(
        default=None, description="Whether a course is still being offered."
    )

    transfer_destinations: Optional[str] = Field(
        default=None,
        description="Institutions that a course has transfer agreements to. Stored in csv format.",
    )
    # Funny SQLModel relationships that ARE NOT database relationships
    # course_outlines: list["CourseOutline"] = Relationship() # description="TODO: Course outlines for the course if available."
    # transfers: list["TransferDB"] = Relationship() # description="All transfers for the course."
    # page: "CoursePage" = Relationship(back_populates="course")
    # summaries: list["CourseSummaryDB"] = Relationship(back_populates="course")
    # sections: list["SectionDB"] = Relationship(back_populates="course")


class CourseMaxDB(CourseMax, table=True):
    id: str = Field(
        primary_key=True,
        description="Internal primary and unique key (e.g. CMAX-ENGL-1123).",
    )

    subject: str = Field(index=True, foreign_key="coursedb.subject")
    course_code: str = Field(index=True, foreign_key="coursedb.course_code")

    id_course: str = Field(index=True, foreign_key="coursedb.id")
    course: "CourseDB" = Relationship(
        back_populates="attributes",
        sa_relationship_kwargs={
            "primaryjoin": "CourseMaxDB.id_course==CourseDB.id",
            # "lazy": "selectin",
            "viewonly": True,
        },
    )


class CourseMaxAPI(CourseMax):
    # id: str
    pass


class CourseMaxAPIOnlyTransfers(CourseMax):
    id: str


# class CourseBuiltDB(CourseBase, table=True):
#     subject: str        = Field(primary_key=True, foreign_key="course.subject")
#     course_code: str    = Field(primary_key=True, foreign_key="course.course_code")


# class CourseAPIBuild(CourseBase):

#     # all of these will be removed once the course is returned
#     year: int = Field(default=0)
#     term: int = Field(default=0)


#     offerings: list[SectionAPI]                 = Field(default=[], description="All past offerings of the course")
#     transfers: list[TransferDB]                   = Field(default=[], description="Information on how the course transfers.")

# class CourseAPIExt(CourseBase):
#     offerings: list[SectionAPI]                 = Field(default=[], description="All past offerings of the course")
#     transfers: list[TransferAPI]                   = Field(default=[], description="Information on how the course transfers.")

# class CourseAPI(CourseBase):
#     # offerings: list[SectionAPI]                 = Field(default=[], description="All past offerings of the course")
#     transfers: list[TransferAPI]                   = Field(default=[], description="Information on how the course transfers.")


# class Config:
#     json_schema_extra = {
#         "example": {
#             "RP" : None,
#             "subject" : "CPSC",
#             "course_code" : 1050,
#             "credits" : 3.0,
#             "title": "Introduction to Computer Science",
#             "description" : "Offers a broad overview of the computer science discipline.  Provides students with an appreciation for and an understanding of the many different aspects of the discipline.  Topics include information and data representation; introduction to computer hardware and programming; networks; applications (e.g., spreadsheet, database); social networking; ethics; and history.  Intended for both students expecting to continue in computer science as well as for those taking it for general interest.",
#             "hours": {
#                 "lecture": 4,
#                 "seminar": 0,
#                 "lab": 2
#             },
#             "add_fees" : 34.,
#             "rpt_limit" : 2,
#             # TODO: fix attributes
#             # "attributes" : {
#             #     "2AR" : False,
#             #     "2SC" : False,
#             #     "HUM" : False,
#             #     "LSC" : False,
#             #     "SCI" : True,
#             #     "SOC" : False,
#             #     "UT" :  True,
#             # },
#             "transfer" : [
#                 Transfer.Config.json_schema_extra["example1"],
#                 Transfer.Config.json_schema_extra["example2"]
#                 ],
#         }
#     }
