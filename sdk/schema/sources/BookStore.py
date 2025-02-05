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


class BookStore(SQLModel):
    id: int = Field(primary_key=True)
    isbn: str = Field(
        description="ISBN of the book. eg. ```9780357508138```.",
    )  # not primary key because it have '' as a value sometimes and maybe possible same isbn book for multiple courses
    title: str = Field(
        description="Title of the book. eg. ```CompTIA Network+ Guide to Networks, 9E```."
    )
    authors: str = Field(description="Authors of the book. eg. ```West```.")
    edition: str = Field(description="Edition of the book. eg. ```Edition 9```.")
    binding: str = Field(
        description="Binding of the book. eg. ```Paperback```, ```Digital Version```."
    )
    cover_img_url: str = Field(
        description="URL of the cover image of the book. eg. ```https://mycampusstore.langara.bc.ca/cover_image.asp?Key=9780357508138&Size=M&p=1```."
    )
    required: bool = Field(
        description="Whether the book is required for the course. eg. ```false```."
    )


class BookStoreDB(BookStore, table=True):
    subject: str = Field(index=True, foreign_key="coursedb.subject")  # dept id
    course_code: str = Field(
        index=True, foreign_key="coursedb.course_code"
    )  # course code
    section: str = Field(index=True, foreign_key="sectiondb.section")


class BookStoreList(SQLModel):
    books: list[BookStore]
