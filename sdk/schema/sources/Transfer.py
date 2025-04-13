from typing import TYPE_CHECKING

from requests_cache import Optional
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from sdk.schema.aggregated.Course import CourseDB


class Transfer(SQLModel):
    id: str = Field(
        primary_key=True,
        description="Internal primary and unique key (e.g. TNFR-ENGL-1123-UBCV-309967).",
    )

    source: str = Field(description="Source institution code e.g. ````LANG```.")
    source_credits: Optional[float] = Field(
        description="Credits at the source institution."
    )
    source_title: Optional[str] = Field(
        description="Course title at the source institution."
    )

    destination: str = Field(
        index=True, description="Destination institution code e.g. ```SFU```."
    )
    destination_name: str = Field(
        description="Destination institution full name e.g. ```Simon Fraser University```."
    )

    credit: str = Field(
        index=True,
        description="How many credits is the course worth at the source institution.",
    )
    condition: Optional[str] = Field(
        description="Additional conditions that apply to the credit transfer."
    )

    effective_start: str = Field(description="When this transfer agreement began.")
    effective_end: Optional[str] = Field(
        index=True, description="When the transfer agreement ended."
    )

    # class Config:
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "subject": "CPSC",
                    "course_code": 1050,
                    "source": "LANG",
                    "destination": "ALEX",
                    "credit": "ALEX CPSC 1XX (3)",
                    "effective_start": "Sep/15",
                    "effective_end": None
                },
                {
                    "subject": "CPSC",
                    "course_code": 1050,
                    "source": "LANG",
                    "destination": "AU",
                    "credit": "AU COMP 2XX (3)",
                    "effective_start": "May/15",
                    "effective_end": None
                }
            ]
        }
    }
        

class TransferDB(Transfer, table=True):
    transfer_guide_id: int = Field(
        index=True,
        description="Internal id that BCTransferGuide uses for transfer agreements",
    )

    # 1:many relationship with course
    subject: str = Field(index=True, foreign_key="coursedb.subject")
    course_code: str = Field(index=True, foreign_key="coursedb.course_code")

    id_course: str = Field(index=True, foreign_key="coursedb.id")

    course: "CourseDB" = Relationship(
        back_populates="transfers",
        sa_relationship_kwargs={
            "primaryjoin": "TransferDB.id_course==CourseDB.id",
            "viewonly": True,
        },
    )


class TransferAPI(Transfer):
    subject: str
    course_code: str


class TransferAPIList(SQLModel):
    transfers: list[TransferAPI]
