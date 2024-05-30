from sqlmodel import Field, SQLModel

class Transfer(SQLModel, table=True):
    subject: str            = Field(primary_key=True, description="Subject area e.g. ```CPSC```.")
    course_code: int        = Field(primary_key=True, description="Course code e.g. ```1050```.")     
    source: str             = Field(primary_key=True, description="Source institution e.g. ````LANG```.")
    destination: str        = Field(primary_key=True, description="Destination instituation e.g. ```SFU```.")
    credit: str             = Field(primary_key=True, description="How many credits at the destination.")
    effective_start: str    = Field(primary_key=True, description="When this transfer agreement began.")
    effective_end: str      = Field(primary_key=True, description="When the transfer agreement ended.")
    
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