from typing import List, Optional

from sqlalchemy import UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlmodel import Field, Relationship, SQLModel

Base = declarative_base()


class BookstoreBase(SQLModel):
    subject: str = Field(foreign_key="coursedb.subject")
    course_code: str = Field(foreign_key="coursedb.course_code")
    section: str = Field(foreign_key="sectiondb.section")


class BookstoreDB(BookstoreBase, table=True):
    id: int = Field(primary_key=True)  # Auto-increment primary key
    bookdb_id: int = Field(foreign_key="bookdb.id")

    __table_args__ = (
        UniqueConstraint(
            "subject",
            "course_code",
            "section",
            "bookdb_id",
            name="bookstore_bookid_uc",
        ),
    )

    # View-only relationship to BookDB
    books: List["BookDB"] = Relationship(
        back_populates="bookstore",
        sa_relationship_kwargs={
            "primaryjoin": "BookstoreDB.bookdb_id==BookDB.id",
            "viewonly": True,
        },
    )


class BookBase(SQLModel):
    id: int = Field(primary_key=True)
    isbn: str = Field(description="ISBN of the book.")
    title: str = Field(description="Title of the book.")
    authors: str = Field(description="Authors of the book.")
    edition: Optional[str] = Field(default=None, description="Edition of the book.")
    binding: Optional[str] = Field(
        default=None, description="Binding type of the book."
    )
    cover_img_url: Optional[str] = Field(default=None, description="Cover image URL.")
    required: bool = Field(default=False, description="Is the book required?")


class BookDB(BookBase, table=True):
    # View-only relationship to BookstoreDB
    bookstore: List["BookstoreDB"] = Relationship(
        back_populates="books",
        sa_relationship_kwargs={
            "primaryjoin": "BookstoreDB.bookdb_id==BookDB.id",
            "viewonly": True,
        },
    )


# misc


class BookAPI(BookBase):
    bookstore: List["BookstoreBase"]

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "isbn": "9780357508138",
                "title": "CompTIA Network+ Guide to Networks, 9E",
                "authors": "West",
                "edition": "Edition 9",
                "binding": "Paperback",
                "cover_img_url": "https://mycampusstore.langara.bc.ca/cover_image.asp?Key=9780357508138&Size=M&p=1",
                "required": False,
                "bookstore": [
                    {
                        "id": 1,
                        "subject": "CPSC",
                        "course_code": "1480",
                        "section": "M01",
                    }
                ],
            }
        }


class BookAPIList(SQLModel):
    books: List[BookAPI]
