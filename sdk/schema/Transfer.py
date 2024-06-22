from requests_cache import Optional
from sqlmodel import Field, Relationship, SQLModel

from sdk.schema.BaseModels import Course


class Transfer(SQLModel):  
    id: str     = Field(primary_key=True, description="Internal primary and unique key (e.g. TNFR-ENGL-1123-UBCV-309967).")
    
    transfer_guide_id: int          = Field(index=True, description="Internal id that BCTransferGuide uses for transfer agreements") 
    
    source: str                     = Field(description="Source institution code e.g. ````LANG```.")
    source_credits: Optional[float] = Field(description="Credits at the source institution.")
    source_title : Optional[str]    = Field(description="Course title at the source institution.")
    
    destination: str                = Field(index=True, description="Destination institution code e.g. ```SFU```.")
    destination_name: str           = Field(description="Destination institution full name e.g. ```Simon Fraser University```.")

    credit: str                     = Field(index=True, description="How many credits is the course worth at the source institution.")    
    condition: Optional[str]        = Field(description="Additional conditions that apply to the credit transfer.")
    
    effective_start: str            = Field(description="When this transfer agreement began.")
    effective_end: Optional[str]    = Field(description="When the transfer agreement ended.")
    
    class Config:
        
        json_schema_extra = {
            "example1": {
                 "subject": "CPSC",
                "course_code": 1050,
                "source": "LANG",
                "destination": "ALEX",
                "credit": "ALEX CPSC 1XX (3)",
                "effective_start": "Sep/15",
                "effective_end": None
            },
            "example2": {
                "subject": "CPSC",
                "course_code": 1050,
                "source": "LANG",
                "destination": "AU",
                "credit": "AU COMP 2XX (3)",
                "effective_start": "May/15",
                "effective_end": None
            }
        }
        

class TransferDB(Transfer, table=True):
    # 1:many relationship with course
    subject: str        = Field(index=True, foreign_key="course.subject")
    course_code: int    = Field(index=True, foreign_key="course.course_code")
    
    id_course: str      = Field(index=True, foreign_key="course.id")
    id_course_max : str = Field(index=True, foreign_key="coursemaxdb.id")
    # course: Course = Relationship(
    #     sa_relationship_kwargs={"primaryjoin": "TransferDB.subject==Course.subject and TransferDB.course_code==Course.course_code", "lazy": "joined"}
    # )
        
    

class TransferAPI(Transfer):
    subject: str
    course_code: int
    