from sqlmodel import Field,  SQLModel


class Metadata(SQLModel, table=True):
    field: str = Field(primary_key=True, description="Field.")
    value: str = Field(description="Value of field")
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "field": "last_updated",
                    "value": "2024-10-30T12:00:00Z"
                },
                {
                    "field": "db_version",
                    "value": "2"
                }
            ]
        }