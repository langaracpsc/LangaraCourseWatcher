from typing import Optional

from sqlmodel import Field, Relationship, SQLModel


class Semester(SQLModel, table=True):
    id: str     = Field(primary_key=True, description="Internal primary key (e.g. SMTR-2024-30).")
    
    year: int   = Field(index=True, description='Year e.g. ```2024```.')
    term: int   = Field(index=True, description='Term e.g. ```30```')
    
    courses_first_day: Optional[str] = Field(default=None, description="First day of normal classes.")
    courses_last_day: Optional[str] = Field(default=None, description="Last day of normal classes.")
    
    # sections: list["SectionDB"] = Relationship()
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "id": "SMTR-2024-30",
                    "year": 2024,
                    "term": 30,
                    "courses_first_day": "2024-9-02",
                    "courses_last_day": "2024-12-10"
                },
                {
                    "id": "SMTR-2025-10",
                    "year": 2025,
                    "term": 10,
                    "courses_first_day": "2025-01-02",
                    "courses_last_day": "2025-04-10"
                }
            ]
        }
