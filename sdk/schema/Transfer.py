from requests_cache import Optional
from sqlmodel import Field, SQLModel


class Transfer(SQLModel):
    subject: str            = Field(index=True, description="Subject area e.g. ```CPSC```.")
    course_code: int        = Field(index=True, description="Course code e.g. ```1050```.")     
    source: str             = Field(description="Source institution e.g. ````LANG```.")
    destination: str        = Field(description="Destination instituation e.g. ```SFU```.")
    credit: str             = Field(description="How many credits at the destination.")
    condition: Optional[str]          = Field()
    effective_start: str    = Field(description="When this transfer agreement began.")
    effective_end: Optional[str]      = Field(description="When the transfer agreement ended.")
    
    class Config:
        
        json_schema_extra = {
            "example1": {
                 "subject": "CPSC",
                "course_code": 1050,
                "source": "LANG",
                "destination": "ALEX",
                "credit": "ALEX CPSC 1XX (3)",
                "effective_start": "Sep/15",
                "effective_end": "present"
            },
            "example2": {
                "subject": "CPSC",
                "course_code": 1050,
                "source": "LANG",
                "destination": "AU",
                "credit": "AU COMP 2XX (3)",
                "effective_start": "May/15",
                "effective_end": "present"
            }
        }
        

class TransferDB(Transfer, table=True):
    id: str             = Field(primary_key=True, description="Unique identifier for each transfer.")
    course_id:str       = Field(primary_key=True, description="Unique identifier for each Course.")
    
class TransferAPI(Transfer):
    id: str
    