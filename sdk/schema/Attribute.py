from enum import Enum
from sqlmodel import Field, SQLModel


class Attribute(SQLModel):
    subject: str        = Field(primary_key=True, description="Subject area e.g. ```CPSC```.")
    course_code: int    = Field(primary_key=True, description="Course code e.g. ```1050```.")   
    
    attr_ar: bool   =Field(default=False, description="Second year arts course.")
    attr_sc: bool   =Field(default=False, description="Second year science course.")
    attr_hum: bool  =Field(default=False, description="Humanities course.")
    attr_lsc: bool  =Field(default=False, description="Lab science course.")
    attr_sci: bool  =Field(default=False, description="Science course.")
    attr_soc: bool  =Field(default=False, description="SOC course.")
    attr_ut: bool   =Field(default=False, description="University transferrable course.")
    

class AttributeDB(Attribute, table=True):
    year: int                       = Field(primary_key=True, description='Year e.g. ```2024```.')
    term: int                       = Field(primary_key=True, description='Term e.g. ```30```')