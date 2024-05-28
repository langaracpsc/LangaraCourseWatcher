from sqlalchemy import Column, Integer, String, Boolean, Float, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Session
from sqlalchemy import Integer, String, Float, Text, Boolean, ForeignKey, Table
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.orm import mapped_column

class Base(DeclarativeBase):
    pass


class Transfer(Base):
    __tablename__ = 'Transfer'
    subject = mapped_column(String, primary_key=True)
    course_code = mapped_column(Integer, primary_key=True)
    source = mapped_column(String, primary_key=True)
    destination = mapped_column(String, primary_key=True)
    credit = mapped_column(Float)
    effective_start = mapped_column(String, primary_key=True)
    effective_end = mapped_column(String, primary_key=True)

class Course(Base):
    __tablename__ = 'Course'
    subject = mapped_column(String, primary_key=True)
    course_code = mapped_column(Integer, primary_key=True)
    credits = mapped_column(Float)
    title = mapped_column(String)
    description = mapped_column(Text)
    lecture_hours = mapped_column(Integer)
    seminar_hours = mapped_column(Integer)
    lab_hours = mapped_column(Integer)
    AR = mapped_column(Boolean)
    SC = mapped_column(Boolean)
    HUM = mapped_column(Boolean)
    LSC = mapped_column(Boolean)
    SCI = mapped_column(Boolean)
    SOC = mapped_column(Boolean)
    UT = mapped_column(Boolean)

class Section(Base):
    __tablename__ = 'Section'
    year = mapped_column(Integer, primary_key=True)
    term = mapped_column(String, primary_key=True)
    RP = mapped_column(String, primary_key=True)
    seats = mapped_column(Integer, primary_key=True)
    waitlist = mapped_column(Integer, primary_key=True)
    crn = mapped_column(Integer, primary_key=True)
    subject = mapped_column(String)
    course_code = mapped_column(Integer)
    section = mapped_column(String)
    credits = mapped_column(Float)
    title = mapped_column(String)
    additional_fees = mapped_column(Float)
    repeat_limit = mapped_column(Integer)
    notes = mapped_column(Text)

class Schedule(Base):
    __tablename__ = 'Schedule'
    year = mapped_column(Integer, primary_key=True)
    term = mapped_column(String, primary_key=True)
    section = section = mapped_column(String, primary_key=True)
    
    crn = mapped_column(Integer, primary_key=True)
    type = mapped_column(String, primary_key=True)
    days = mapped_column(String, primary_key=True)
    time = mapped_column(String, primary_key=True)
    start_date = mapped_column(String, primary_key=True)
    end_date = mapped_column(String, primary_key=True)
    room = mapped_column(String, primary_key=True)
    instructor = mapped_column(String, primary_key=True)


class SemesterHTML(Base):
    __tablename__ = 'SemesterHTML'
    year = mapped_column(Integer, primary_key=True)
    term = mapped_column(String, primary_key=True)
    sectionHTML = mapped_column(Text)
    catalogueHTML = mapped_column(Text)
    attributeHTML = mapped_column(Text)

class TransferPDF(Base):
    __tablename__ = 'TransferPDF'
    subject = mapped_column(String, primary_key=True)
    pdf = mapped_column(Text)




from sqlalchemy import create_engine
engine = create_engine("sqlite://", echo=True)
Base.metadata.create_all(engine)


with Session(engine) as session:
    c1 = Course(subject="CPSC", course_code=1000)
    c2 = Course(subject="CPSC", course_code=2000)
    
    session.add_all([c1, c2])
    session.commit()