from typing import List, Optional

from sqlalchemy import ForeignKey, ForeignKeyConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlmodel import Field, Relationship, SQLModel

"""
    "CPSC|||1480|||M01": {
        "Course Name": "CPSC - 1480, section M01 (ALL)",
        "Note": "The textbook for this course is available in two formats: print and eText (digital).  Please choose one of the options below.",
        "Book List": [
            {
                "cover_img_url": "https://mycampusstore.langara.bc.ca/cover_image.asp?Key=9780357508138&Size=M&p=1",
                "title": "CompTIA Network+ Guide to Networks, 9E",
                "authors": "West",
                "isbn": "9780357508138",
                "edition": "Edition 9",
                "binding": "Paperback",
                "required": false
            },
            {
                "cover_img_url": "https://mycampusstore.langara.bc.ca/outerweb/product_images/9780357709580l.png",
                "title": "CEI Access Code, eText for CompTIA Network+ Guide to Networks (1 year), 9E",
                "authors": "West",
                "isbn": "9780357709580",
                "edition": "Edition 9",
                "binding": "Digital Version",
                "required": false
            }
        ]
    }
"""


Base = declarative_base()

# TODO: Give proper database table name eg. BookDB


class BookstoreBookLink(SQLModel, table=True):
    subject: str = Field(primary_key=True)
    course_code: str = Field(primary_key=True)
    section: str = Field(primary_key=True)
    book_db_id: str = Field(ForeignKey("book.id"), primary_key=True)

    __table_args__ = (
        ForeignKeyConstraint(
            ["subject", "course_code", "section"],
            ["bookstore.subject", "bookstore.course_code", "bookstore.section"],
        ),
    )


class Book(SQLModel, table=True):
    id: int = Field(primary_key=True)
    isbn: str = Field(
        description="ISBN of the book."
    )  # XXX: some book entry are lab manual and stuff with no ISBN.
    title: str = Field(description="Title of the book.")
    authors: str = Field(description="Authors of the book.")
    edition: Optional[str] = Field(default=None, description="Edition of the book.")
    binding: Optional[str] = Field(
        default=None, description="Binding type of the book."
    )
    cover_img_url: Optional[str] = Field(default=None, description="Cover image URL.")
    required: bool = Field(
        default=False, description="Is the book required for the bookstore listing?"
    )

    bookstores: List["Bookstore"] = Relationship(
        back_populates="books",
        link_model=BookstoreBookLink,
        sa_relationship_kwargs={
            "primaryjoin": "Book.id == foreign(BookstoreBookLink.book_db_id)",
            "secondaryjoin": "and_(foreign(BookstoreBookLink.subject) == Bookstore.subject, "
            "foreign(BookstoreBookLink.course_code) == Bookstore.course_code, "
            "foreign(BookstoreBookLink.section) == Bookstore.section)",
        },
    )


class Bookstore(SQLModel, table=True):
    subject: str = Field(primary_key=True, max_length=50)
    course_code: str = Field(primary_key=True, max_length=10)
    section: str = Field(primary_key=True, max_length=10)

    books: List[Book] = Relationship(
        back_populates="bookstores",
        link_model=BookstoreBookLink,
        sa_relationship_kwargs={
            "primaryjoin": "and_(foreign(BookstoreBookLink.subject) == Bookstore.subject, "
            "foreign(BookstoreBookLink.course_code) == Bookstore.course_code, "
            "foreign(BookstoreBookLink.section) == Bookstore.section)",
            "secondaryjoin": "Book.id == foreign(BookstoreBookLink.book_db_id)",
        },
    )


# misc


class BookList(SQLModel):
    books: List[Book]
