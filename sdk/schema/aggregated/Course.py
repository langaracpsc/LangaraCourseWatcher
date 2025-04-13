from typing import TYPE_CHECKING, List

from sqlmodel import Field, Relationship, SQLModel

# if TYPE_CHECKING:
from sdk.schema.aggregated.CourseMax import CourseMaxAPI, CourseMaxDB
from sdk.schema.sources.CourseOutline import CourseOutlineAPI, CourseOutlineDB
from sdk.schema.sources.Section import SectionAPI, SectionDB
from sdk.schema.sources.Transfer import TransferAPI, TransferDB


class CourseBase(SQLModel):
    subject: str = Field(index=True, description="Subject area e.g. ```CPSC```.")
    course_code: str = Field(index=True, description="Course code e.g. ```1050```.")


class CourseDB(CourseBase, table=True):
    id: str = Field(
        primary_key=True, description="Internal primary key (e.g. CRSE-ENGL-1123)."
    )

    sections: List["SectionDB"] = Relationship(
        # back_populates="course",
        sa_relationship_kwargs={
            "primaryjoin": "SectionDB.id_course==CourseDB.id",
            # "lazy": "selectin",
            "viewonly": True,
        }
    )

    transfers: List["TransferDB"] = Relationship(
        # back_populates="course",
        sa_relationship_kwargs={
            "primaryjoin": "TransferDB.id_course==CourseDB.id",
            "lazy": "selectin",
            "viewonly": True,
        }
    )

    attributes: "CourseMaxDB" = Relationship(
        # back_populates="course",
        sa_relationship_kwargs={
            "primaryjoin": "CourseMaxDB.id_course==CourseDB.id",
            "lazy": "selectin",
            "viewonly": True,
        }
    )

    outlines: List["CourseOutlineDB"] = Relationship(
        # back_populates="course",
        sa_relationship_kwargs={
            "primaryjoin": "CourseOutlineDB.id_course==CourseDB.id",
            "lazy": "selectin",
            "viewonly" : True
        })
    


class CourseAPI(CourseBase):
    id: str
    attributes: "CourseMaxAPI" = None
    sections: List["SectionAPI"] = []
    transfers: List["TransferAPI"] = []
    outlines: List["CourseOutlineAPI"] = []
    
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id" : "CRSE-ENGL-1123",
                    "subject" : "ENGL",
                    "course_code" : "1123",
                    
                    "attributes" : CourseMaxAPI.model_config["json_schema_extra"]["examples"][0],
                    
                    "sections" : SectionAPI.model_config["json_schema_extra"]["examples"],
                    
                    "transfers" : TransferAPI.model_config["json_schema_extra"]["examples"],
                    
                    "outlines" : [
                        CourseOutlineAPI.model_config["json_schema_extra"]["examples"][0] 
                    ]
                }
            ]
        }
    }
    


class CourseAPILight(CourseBase):
    id: str
    attributes: "CourseMaxAPI" = {}
    transfers: List["TransferAPI"] = []
    outlines: List["CourseOutlineAPI"] = []


class CourseAPIAttributes(CourseBase):
    id: str
    attributes: "CourseMaxAPI" = {}


class CourseAPILightList(SQLModel):
    courses: list[CourseAPILight]
