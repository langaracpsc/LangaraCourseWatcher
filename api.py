from contextlib import asynccontextmanager
import os
import sys
import logging
from datetime import datetime
from typing import Annotated, Any, Optional

from fastapi.encoders import jsonable_encoder
import orjson

from sqlalchemy import distinct
import fastapi_cache
from pydantic import BaseModel

from sdk.schema.aggregated.Metadata import Metadata

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

screen_handler = logging.StreamHandler()
formatter = logging.Formatter(fmt='[%(asctime)s] : [%(levelname)-8s] : %(message)s',
                                datefmt='%Y-%m-%d %H:%M:%S')
screen_handler.setFormatter(formatter)
logger.addHandler(screen_handler)


from fastapi import FastAPI, HTTPException, Query, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse

from sqlmodel import SQLModel, Session, col, create_engine, select
from sqlalchemy.orm import selectinload
from sqlalchemy import Engine, Integer, and_, cast, exists, func, or_, text

# caching stuff
from contextlib import asynccontextmanager
from typing import AsyncIterator, Dict, Optional
from fastapi_cache import Coder, FastAPICache, KeyBuilder
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.decorator import cache

# DATABASE STUFF
from sdk.schema.sources.CourseAttribute import CourseAttributeDB
from sdk.schema.sources.CourseOutline import CourseOutlineDB
from sdk.schema.sources.CoursePage import CoursePageDB
from sdk.schema.sources.CourseSummary import CourseSummaryDB
from sdk.schema.sources.ScheduleEntry import ScheduleEntryDB
from sdk.schema.sources.Section import SectionAPIList, SectionDB, SectionAPI
from sdk.schema.sources.Transfer import TransferAPI, TransferAPIList, TransferDB

from sdk.schema.aggregated.Course import CourseAPI, CourseAPILight, CourseAPILightList, CourseDB
from sdk.schema.aggregated.Semester import Semester

# RESPONSE STUFF
from sdk.schema.aggregated.ApiResponses import ExportCourseList, ExportSectionList, IndexCourse, IndexCourseList, IndexSemesterList, IndexSubjectList, IndexTransfer, IndexTransferList, MetadataFormatted, PaginationPage, SearchCourse, SearchCourseList, SearchSectionList
from sdk.schema.aggregated.CourseMax import CourseMaxAPI, CourseMaxAPIOnlyTransfers, CourseMaxDB


DB_LOCATION="database/database.db"
ARCHIVES_DIRECTORY="database/archives/"

from dotenv import load_dotenv
load_dotenv()


# database controller

DB_TYPE = "sqlite"
CACHE_DB_TO_MEMORY = True

sql_address = f'{DB_TYPE}:///{DB_LOCATION}'
connect_args = {"check_same_thread": False}
engine: Engine = None
engine_initialized = False

def fetchDB():
    global engine
    global engine_initialized
    
    # prevent memory leak of old in-memory database
    if engine_initialized:
        engine.dispose()
        
    if CACHE_DB_TO_MEMORY:
        # file system database
        engine_source = create_engine(sql_address, connect_args=connect_args)

        # in memory database
        engine_memory = create_engine('sqlite://', connect_args=connect_args)

        raw_connection_memory = engine_memory.raw_connection()
        raw_connection_source = engine_source.raw_connection()

        raw_connection_source.backup(raw_connection_memory.connection)
        raw_connection_source.close()
        
        engine = engine_memory
        
        journal_options = (
            "PRAGMA synchronous = OFF;",
            "pragma cache_size = 100000",
        )
        
    else:
        engine = create_engine(sql_address, connect_args=connect_args)
        
        journal_options = (
            # "pragma synchronous = normal;",
            # "pragma journal_size_limit = 6144000;",
            # "pragma mmap_size = 30000000000;",
            # "pragma page_size = 32768;",
            # "pragma cache_size = 100000",
            "pragma vacuum;",
            "pragma optimize"
            # "pragma temp_store = memory;",
        )
    
    # SQLModel.metadata.create_all(engine)
        
    with Session(engine) as session:
        for pragma in journal_options:
            session.exec(text(pragma))
    
    engine_initialized = True
    return engine

engine = fetchDB()
def get_session():
    with Session(engine) as session:
        yield session
            
# === MISC. ===

# Define a better custom key builder for fastapi-cache
# the default keybuilder uses the the function arguments
# which doesn't work well with the use of session everywhere.
def better_key_builder(
    func,
    namespace: str = "",
    request: Request = None,
    response: Response = None,
    *args,
    **kwargs,
):
    kwargs = kwargs["kwargs"]
    if "session" in kwargs:
        del kwargs["session"]
    
    # k = kwargs.encode().hexdigest()
    k = [f"{key}={value}" for key, value in sorted(kwargs.items())]
    k = "".join(k)
    # print(k)
    
    
    key = ":".join([
        namespace,
        request.method.lower(),
        request.url.path,
        repr(sorted(request.query_params.items())),
        k
    ])
    
    # print(key)
    
    return key

# We also need to define our own coder because by 
class BetterCoder(Coder):
    
    @classmethod
    def encode(cls, value: BaseModel) -> bytes:
        
        # TODO: fix skill issue
        # I keep getting errors when trying to serialize other stuff so lets make it easy
        if not isinstance(value, BaseModel):
            raise TypeError("Value must be an instance of BaseModel.")
        
        # we have to set the serialize_as_any parameter to true
        # otherwise the pydantic serialization will not include nested classes
        # you should be able to set this by class, but I could not get that working
        print(value)
        print(type(value))
        
        return value.model_dump_json(serialize_as_any=True)
        return orjson.dumps(
            value,
            default=jsonable_encoder,
            option=orjson.OPT_NON_STR_KEYS | orjson.OPT_SERIALIZE_NUMPY,
            serialize_as_any=True
        )

    @classmethod
    def decode(cls, value: bytes) -> Any:
        return orjson.loads(value)



# === STARTUP STUFF ===



# === FASTAPI STARTUP STUFF ===
@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        
    if (os.path.exists(DB_LOCATION)):
        logger.info("Database found.")
    else:
        logger.error("Database not found. Exiting.")
        sys.exit(-1)
    
    FastAPICache.init(InMemoryBackend(), key_builder=better_key_builder,  expire=3600)  
    logger.info("Cache initialized.")     
    
     
    
    yield

description = "Gets course data from the Langara website. Data refreshes every 30 minutes. All data belongs to Langara College or BC Transfer Guide and is summarized here in order to help students. Pull requests welcome!"

app = FastAPI(
    title="Langara Courses API.",
    description=description,
    redoc_url="/",
    version="1.1",
    lifespan=lifespan
    )

# gzip responses above 500 bytes
app.add_middleware(GZipMiddleware, minimum_size=500) 

origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FAVICON_PATH = "favicon.ico"
@app.get('/favicon.ico', include_in_schema=False)
# @cache()
async def favicon():
    return FileResponse(FAVICON_PATH)


# ==== ROUTES ====

@app.get(
    "/v1/index/latest_semester",
    summary="Latest semester.",
    description="Returns the latest semester from which data is available",
    response_model=Semester
)
@cache()
async def index_latest_semester(
    *,
    session: Session = Depends(get_session),
) -> Semester:
    
    statement = select(Semester).order_by(col(Semester.year).desc(), col(Semester.term).desc()).distinct().limit(1)
    results = session.exec(statement)
    result = results.first()
    
    if result == None:
        raise HTTPException(status_code=500, detail="No semesters found in database. Contact an administrator.")

    
    return result




@app.get(
    "/v1/index/semesters",
    summary="All semesters.",
    description="Returns all semesters from which data is available",
    response_model=IndexSemesterList
)
@cache()
async def index_semesters(
    *,
    session: Session = Depends(get_session),
) -> IndexSemesterList:
    
    statement = select(Semester
        ).order_by( col(Semester.year).desc(), col(Semester.term).desc()
        ).distinct()
    results = session.exec(statement)
    result = results.all()
    
    return IndexSemesterList(
        count = len(result),
        semesters = result
    )
    

@app.get(
    "/v1/index/subjects",
    summary="All subjects.",
    description="Returns all known subjects. Note that some subjects may have zero course offerings.",
    response_model=IndexSubjectList
)
@cache()
async def index_semesters(
    *,
    session: Session = Depends(get_session),
) -> IndexSubjectList:
    
    statement = select(CourseMaxDB.subject
        ).order_by( CourseMaxDB.subject.asc()
        ).distinct()
    results = session.exec(statement)
    result = results.all()
    
    return IndexSubjectList(
        count = len(result),
        subjects = result
    )


@app.get(
    "/v1/index/courses",
    summary="All courses.",
    description="Returns all known courses.",
    # you shouldn't need to use this route
    # getting all course info is pretty fast
    include_in_schema=False 
    # response_model=IndexCourseList
)
@cache()
async def index_courses(
    *,
    session: Session = Depends(get_session),
):
    
    statement = select(CourseMaxDB.subject, CourseMaxDB.course_code, CourseMaxDB.title, CourseMaxDB.abbreviated_title, CourseMaxDB.active).order_by(col(CourseMaxDB.subject).asc(), col(CourseMaxDB.course_code).asc())
    results = session.exec(statement)
    result = results.all()
    
    if len(result) == 0:
        statement = select(CourseDB.subject, CourseDB.course_code)
        results = session.exec(statement)
        result = list(results.all())
        
        return result
    
    courses:list[IndexCourse] = []
    subjects = []
    
    for r in result:
        if r.subject not in subjects:
            subjects.append(r.subject)
        
        t = r.title
        if t == None:
            t = r.abbreviated_title
        
        c = IndexCourse(
            subject=r.subject,
            course_code=r.course_code,
            title=t,
            active=r.active
        )
        courses.append(c)
    
    return IndexCourseList(
        subject_count = len(subjects),
        course_count = len(courses),
        courses = courses
    )


@app.get(
    "/v1/index/transfer_destinations",
    summary="All transfer destination institutions.",
    description="Returns a list of all known transfer destination institutions.",
    response_model=IndexTransferList,
)
@cache()
async def index_transfer_destinations(
    *,
    session: Session = Depends(get_session),
) -> IndexTransferList:
    statement = select(TransferDB.destination, TransferDB.destination_name).distinct().order_by(TransferDB.destination_name)
    results = session.exec(statement)
    destinations = results.all()
    
    out: list[IndexTransfer] = []
    
    for dest in destinations:
        out.append(IndexTransfer(code=dest[0], name=dest[1]))
    
    return IndexTransferList(transfers=out)





@app.get(
    "/v1/semester/{year}/{term}/courses",
    summary="Semester course data.",
    description="Returns the courses available for a given semester.",
    response_model=CourseAPILightList
)
@cache()
async def semester(
    *,
    session: Session = Depends(get_session),
    year: int, 
    term: int
) -> CourseAPILightList:
    # get any course where there is at least one section
    # that is in the current year and term
    
    
    statement = (
        select(SectionDB.id_course)
        .where(SectionDB.year == year, SectionDB.term == term)
        .distinct()
    )
    result = session.exec(statement)
    course_ids = result.all()
    
    statement = (
        select(CourseDB)
        .where(CourseDB.id.in_(course_ids))
    )
    result = session.exec(statement)
    courses = result.all()
    
    return CourseAPILightList(courses=courses)


@app.get(
    "/v1/semester/{year}/{term}/sections",
    summary="Semester section data.",
    description="Returns all sections of a semester",
    response_model=SectionAPIList
)
@cache()
async def semester(
    *,
    session: Session = Depends(get_session),
    year: int, 
    term: int
) -> SectionAPIList:
    
    
    statement = select(SectionDB).where(
            SectionDB.year == year,
            SectionDB.term == term
        )
    
    results = session.exec(statement)
    sections = results.all()
    
    return SectionAPIList(sections=sections)


@app.get(
    "/v1/courses/{subject}/{course_code}",
    summary="Course information.",
    description="Get all available information for a given course.",
    response_model=CourseAPI,
)
@cache()
async def semesterCoursesInfo(
    *,
    session: Session = Depends(get_session),
    subject: str, 
    course_code: str
) -> CourseAPI:
    subject = subject.upper()
    
    statement = select(CourseDB).where(
        CourseDB.subject == subject,
        CourseDB.course_code == course_code
    )
    result = session.exec(statement).first()
    
    if result == None:
        raise HTTPException(status_code=404, detail="Course not found.")
    
    # return result
    # TODO: fix the awful default caching that can't handle SQLModel objects properly
    return CourseAPI(subject=result.subject, course_code=result.course_code, id=result.id, attributes=result.attributes, sections=result.sections, transfers=result.transfers, outlines=result.outlines)
    

@app.get(
    "/v1/section/{year}/{term}/{crn}",
    summary="Section information.",
    description="Get all available information for a given section.",
    response_model=SectionAPI
)
@cache()
async def semesterSectionsInfo(
    *,
    session: Session = Depends(get_session),
    year: int, 
    term: int, 
    crn: int
):
    statement = select(SectionDB).where(SectionDB.year == year, SectionDB.term == term, SectionDB.crn == crn)
    results = session.exec(statement)
    section = results.first()
    
    if section == None:
        raise HTTPException(status_code=404, detail="Course not found.")
    
    statement = select(ScheduleEntryDB).where(ScheduleEntryDB.year == year, ScheduleEntryDB.term == term, ScheduleEntryDB.crn == crn)
    results = session.exec(statement)
    schedules = results.all()
    
    out = section.model_dump()
    out["schedule"] = []
    
    for s in schedules:
        out["schedule"].append(s.model_dump())
                
    return out

@app.get(
    "/v1/transfers/{institution_code}",
    summary="Transfer information.",
    description="Get all available transfers to a given institution.",
    response_model=TransferAPIList
)
@cache()
async def semesterSectionsInfo(
    *,
    session: Session = Depends(get_session),
    institution_code: str, 
) -> TransferAPIList:
    institution_code = institution_code.upper()
    
    statement = select(TransferDB).where(TransferDB.destination == institution_code).order_by(col(TransferDB.credit).asc())
    results = session.exec(statement)
    transfers = results.all()
    
    if transfers == None:
        raise HTTPException(status_code=404, detail="Institution not found.")

    print("returning transfers")
    return TransferAPIList(transfers=transfers)

@app.get(
    "/v1/search/courses",
    summary="Search for courses.",
    description="Lets you search courses using the server instead of the client",
    response_model=SearchCourseList
)
@cache()
async def semesterSectionsInfo(
    *,
    session: Session = Depends(get_session),
    query: str,
    attr_ar: Optional[bool] = None,
    attr_sc: Optional[bool] = None,
    attr_hum: Optional[bool] = None,
    attr_lsc: Optional[bool] = None,
    attr_sci: Optional[bool] = None,
    attr_soc: Optional[bool] = None,
    attr_ut: Optional[bool] = None,
    # optional list, fastapi is weird about how we have to define it
    transfers_to: Annotated[list[str], Query()] = [],
    # offered_online: Optional[bool] = None,
    active: Optional[bool] = None,
) -> SearchCourseList:  
    """
        Implement custom search engine
        if the boolean is true/false we should only include
        or disclude results
        If it is null then we take no action on that filter.
    """
    
    filters = []
    if attr_ar != None:
        filters.append(CourseMaxDB.attr_ar == attr_ar)
    if attr_sc != None:
        filters.append(CourseMaxDB.attr_sc == attr_sc)
    if attr_hum != None:
        filters.append(CourseMaxDB.attr_hum == attr_hum)
    if attr_lsc != None:
        filters.append(CourseMaxDB.attr_lsc == attr_lsc)
    if attr_sci != None:
        filters.append(CourseMaxDB.attr_sci == attr_sci)
    if attr_soc != None:
        filters.append(CourseMaxDB.attr_soc == attr_soc)
    if attr_ut != None:
        filters.append(CourseMaxDB.attr_ut == attr_ut)
    # if offered_online != None:
    #     filters.append(CourseMaxDB.offered_online == offered_online)
    if active != None:
        filters.append(CourseMaxDB.active == active)
    
    # filter by the query
    # numbers use the LIKE keyword
    # words use instr / .contains
    
    search_terms = query.strip().split()
    
    text_filters = []
    
    for search in search_terms:        
        if search.isspace():
            continue
        
        elif search.isnumeric() and len(search) <= 4:
            filters.append(CourseMaxDB.course_code.like(f"{search}%"))
        
        elif len(search) == 4:
            text_filters.append(CourseMaxDB.subject.contains(search))   
        else:
            text_filters.append(CourseMaxDB.title.contains(search))
            text_filters.append(CourseMaxDB.description.contains(search))
            
    if text_filters:
        filters.append(or_(*text_filters))
    
    # filter by transfer destinations
    
    statement = select(TransferDB.destination).distinct()
    results = session.exec(statement)
    transfers = results.all()
    
    
    
    for institution in transfers_to:
        institution = institution.upper()
        # if institution not in 
        
        if institution not in transfers:
            raise HTTPException(404, f"{institution} is not a valid transfer destination. Get the list from /index/transfer_destinations. Valid destinations are {transfers}")
        
        filters.append(
            CourseMaxDB.transfer_destinations.icontains(institution)
        )
    
    statement = select(CourseMaxDB.active, CourseMaxDB.subject, CourseMaxDB.course_code).where(*filters)
    results = session.exec(statement)
    courses = results.all()
    
    # must convert into class to satisfy the caching library
    subjects = []
    
    out = []
    for c in courses:
        if (c.subject not in subjects):
            subjects.append(c.subject)
        out.append(SearchCourse(subject=c.subject, course_code=c.course_code, active=c.active))
    
    # print(out)
    # TODO: implement real numbers
    return SearchCourseList(subject_count=len(subjects), course_count=len(courses), courses=out)


@app.get(
    "/v1/search/sections",
    summary="Search for sections.",
    description="Lets you search sections using the server instead of the client",
    response_model=SearchSectionList
)
@cache()
async def semesterSectionsInfo(
    *,
    session: Session = Depends(get_session),
    query: Optional[str] = None,
    year: Optional[int] = None,
    term: Optional[int] = None,
    online: Optional[bool] = None
) -> SearchSectionList:
    filters = []
    
    if year:
        filters.append(SectionDB.year == year)
    if term:
        filters.append(SectionDB.term == term)
    
    search_terms = []
    if query:
        search_terms = query.strip().split()
        
    text_filters = []
    
    subject = None
    course_code = None
    
    # we will special case the most frequent request of looking up one course
    # if the first term is a subject
    # and the second term is a course code
    if len(search_terms) == 2 and \
        len(search_terms[0]) == 4 and search_terms[0].isalpha() and \
            search_terms[1].isnumeric():
                filters.append(SectionDB.subject == search_terms[0].upper())
                filters.append(SectionDB.course_code.like(f"{search_terms[1]}%"))
    else: 
        for search in search_terms:        
            if search.isspace():
                continue
            
            if search.isalpha():
                # TODO: make this search heuristic less cringe
                # maybe check if its an actual subject before we decide to only search subjects
                if len(search) == 4:
                    text_filters.append(ScheduleEntryDB.subject.contains(f"{search}"))
                else:
                    text_filters.append(ScheduleEntryDB.instructor.contains(f"{search}"))
                    text_filters.append(SectionDB.abbreviated_title.contains(f"{search}"))
            else:
                text_filters.append(ScheduleEntryDB.room.contains(f"{search}"))
                text_filters.append(ScheduleEntryDB.course_code.contains(f"{search}"))
        
    if text_filters:
        filters.append(or_(*text_filters))
    
    
    
    statement = (
        select(SectionDB)
        .join(SectionDB.schedule)  # Join using the relationship name
        .options(selectinload(SectionDB.schedule))
        .where(*filters)
        .distinct()
    )
    results = session.exec(statement)
    sections = results.all()
    
    subjects = []
    courses= []
    
    out = []
    for s in sections:
        out.append(s.id)
        
        if s.subject not in subjects:
            subjects.append(s.subject)
        if s.subject+s.course_code not in courses:
            courses.append(s.subject+s.course_code)
    
    return SearchSectionList(subject_count=len(subjects), section_count=len(sections), course_count=len(courses), sections=out)


class SectionPage(SQLModel):
    page: int
    sections_per_page: int
    total_sections: int
    total_pages: int
    sections: list[SectionAPI]

@app.get(
    "/v2/search/sections",
    summary="Search for content within a semester.",
    description="Lets you search within a semester using the server instead of the client",
    response_model=SectionPage
)
@cache()
async def semesterSectionsInfo(
    *,
    session: Session = Depends(get_session),
    subject: Optional[str] = None,
    course_code: Optional[int] = None,
    title_search: Optional[str] = None,
    instructor_search: Optional[str] = None,
    year: Optional[int] = None,
    term: Optional[int] = None,
    online: Optional[bool] = None,
    attr_ar: Optional[bool] = None,
    attr_sc: Optional[bool] = None,
    attr_hum: Optional[bool] = None,
    attr_lsc: Optional[bool] = None,
    attr_sci: Optional[bool] = None,
    attr_soc: Optional[bool] = None,
    attr_ut: Optional[bool] = None,
    open_seats: Optional[bool] = None,
    no_waitlist: Optional[bool] = None,
    cancelled: Optional[bool] = None,
    page: int = 1,
    sections_per_page: int = 500,
) -> SectionPage:
    
    """
    General flow for search:
    performance is the #1 requirement. Searches should complete within 200ms.
    
    However, this is difficult because our database schema kind of sucks.
    However we persevere.
    
    The first step is to filter courses.
    That means filtering by attributes and title_search.
    
    Then we take courses that pass those and search through all sections.
    """
    # course search
    filters = []
    
    if subject != None:
        filters.append(CourseMaxDB.subject == subject)
    if course_code != None:
        filters.append(SectionDB.course_code.like(f"{course_code}%"))
    if attr_ar != None:
        filters.append(CourseMaxDB.attr_ar == attr_ar)
    if attr_sc != None:
        filters.append(CourseMaxDB.attr_sc == attr_sc)
    if attr_hum != None:
        filters.append(CourseMaxDB.attr_hum == attr_hum)
    if attr_lsc != None:
        filters.append(CourseMaxDB.attr_lsc == attr_lsc)
    if attr_sci != None:
        filters.append(CourseMaxDB.attr_sci == attr_sci)
    if attr_soc != None:
        filters.append(CourseMaxDB.attr_soc == attr_soc)
    if attr_ut != None:
        filters.append(CourseMaxDB.attr_ut == attr_ut)
    if title_search != None:
        filters.append(CourseMaxDB.title.contains(title_search))
    
    courses = []
    if len(filters) > 0:
        statement = select(CourseMaxDB.subject, CourseMaxDB.course_code).where(*filters)
        results = session.exec(statement)
        courses = results.all()
    
    
    # search sections
    filters = []
    coursematch_filters = []
    for c in courses:
        coursematch_filters.append((SectionDB.subject == c.subject) & (SectionDB.course_code == c.course_code))
    
    if year != None:
        filters.append(SectionDB.year == year)
    if term != None:
        filters.append(SectionDB.term == term)
    if online != None:
        if online:
            filters.append(SectionDB.section.contains("W"))
        else:
            filters.append(~SectionDB.section.contains("W")) # bitwise not operator
    
    if open_seats != None:
        if open_seats:
            filters.append(and_(cast(SectionDB.seats, Integer) > 0, SectionDB.seats != "Cancel"))
        else:
            filters.append(SectionDB.seats <= 0)
            
    if no_waitlist != None:
        if no_waitlist:
            filters.append(or_(SectionDB.waitlist == None, SectionDB.waitlist == 0, SectionDB.waitlist == "N/A"))
        else:
            filters.append(cast(SectionDB.waitlist, Integer) > 0)
            
    if cancelled != None:
        if cancelled:
            filters.append(SectionDB.seats == "Cancel")
        else:
            filters.append(SectionDB.seats != "Cancel")    
    
    # editorial choice to exclude exams where the professor is a proctor
    if instructor_search != None:
        filters.append((ScheduleEntryDB.instructor.contains(instructor_search)) & (ScheduleEntryDB.type != "Exam"))
    
    if coursematch_filters:
        filters.append(or_(*coursematch_filters))
    
    
    
    # handle pagination
    
    # Base query for total count and paginated results
    base_statement = (
    select(SectionDB)
    .join(SectionDB.schedule)  # Join with schedule table
    .where(*filters)  # Filters applied to SectionDB and Schedule
    .distinct()
    .options(selectinload(SectionDB.schedule))  # Eagerly load the schedule relationship
    )

    # Query for counting total sections
    count_statement = (
        select(func.count(distinct(SectionDB.id)))  # Count distinct section IDs
        .select_from(SectionDB)
        .join(SectionDB.schedule)  # Join still needed for filters
        .where(*filters)
    )
    total_sections = session.scalar(count_statement)
    
    # Pagination calculations
    offset = (page - 1) * sections_per_page
    total_pages = (total_sections + sections_per_page - 1) // sections_per_page  # Ceiling division

    # Paginated query
    paginated_statement = (
        base_statement
        .offset(offset)
        .limit(sections_per_page)
    )

    # Fetch sections for the current page
    sections = session.exec(paginated_statement).all()

    return SectionPage(
        page=page,
        sections_per_page=sections_per_page,
        total_sections=total_sections,
        total_pages=total_pages,
        sections=sections
    )


# @app.get(
#     "/v1/search/semester",
#     summary="Search for content within a semester.",
#     description="Lets you search within a semester using the server instead of the client",
#     response_model=list[SectionAPI]
# )
# # @cache()
# async def semesterSectionsInfo(
#     *,
#     session: Session = Depends(get_session),
#     query: str,
#     year: int,
#     term: int,
#     online: Optional[bool] = None
# ):
#     # parse query
    
#     search_terms = query.strip().split()
    
#     course_search_terms = []
#     section_search_terms = []
    
#     for search in search_terms:
        
#         # course code
#         if len(search) == 4 and search.isdigit():
#             course_search_terms.append(search)
        
#         # subject
#         elif len(search) == 4 and search.isalpha():
#             course_search_terms.append(search)
            
#         # elif 
    

@app.get(
    "/v1/export/database.db",
    summary="Raw database.",
    description="Gets compacted version of the database with all information.",
    # response_model=Response,
)
# @cache()
async def getDatabase():
    file_path = "database/prebuilts/compact.db.gz"
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=500, detail="Couldn't find compact.db.gz")
    
    response = FileResponse(file_path)
    response.headers["Content-Encoding"] = "gzip"
    return response

@app.get(
    "/v1/export/courses",
    summary="All courses.",
    description="Get info of all available courses.",
    response_model=ExportCourseList
)
@cache()
async def allCourses(
    *,
    session: Session = Depends(get_session),
    page:int = 1,
    # limit = 150: int
) -> ExportCourseList:
    statement = select(CourseDB)
    results = session.exec(statement)
    courses = results.all()
    
    return ExportCourseList(courses=courses)


# @app.get(
#     "/v1/export/sections",
#     summary="All sections.",
#     description="Get info of all available sections.",
#     response_model=ExportSectionList
# )
# @cache()
# async def allSections(
#     *,
#     session: Session = Depends(get_session),
#     page:int = 1,
#     # limit = 150: int
# ) -> ExportSectionList:
#     statement = select(SectionDB).limit(1000)
#     results = session.exec(statement)
#     sections = results.all()
    
#     return ExportSectionList(sections=sections)


# takes approximately 5 ms per course which is fast
# but not fast enough with ~3000 courses
# 150 * 5 ms = ~750 ms for one page (~19 total pages at time of writing)
@app.get(
    "/v1/export/all",
    summary="All information.",
    description="Get all available information. You probably don't need to use this route.",
    response_model=PaginationPage
)
@cache()
async def allInfo(
    *,
    session: Session = Depends(get_session),
    page:int = 1,
    # limit = 150: int
) -> PaginationPage:
    if page < 1:
        raise HTTPException(status_code=400, detail="Page number must be greater than or equal to 1")

    COURSES_PER_PAGE = 150

    total_courses = session.scalar(select(func.count()).select_from(CourseMaxDB))
    total_pages = (total_courses + COURSES_PER_PAGE - 1) // COURSES_PER_PAGE  # Ceiling division


    if page > total_pages:
        raise HTTPException(status_code=400, detail="Page number must be equal or lesser than total_pages")
    
    
    statement = select(CourseDB).order_by(CourseDB.id).limit(COURSES_PER_PAGE).offset(COURSES_PER_PAGE*page-1) # 0-index page
    results = session.exec(statement)
    courses = results.all()

    p = PaginationPage(
        page=page,
        courses_per_page=COURSES_PER_PAGE,
        total_courses=total_courses,
        total_pages=total_pages,
        courses=courses
    )
    return p


@app.get(
    "/v1/metadata",
    response_model=MetadataFormatted,
    summary="Fetch database metadata",
    description="Returns metadata entries as a dictionary with field names as keys.",
)
async def get_metadata(
    session: Session = Depends(get_session),
) -> MetadataFormatted:
    # Query all metadata entries
    metadata_entries = session.exec(select(Metadata)).all()
    
    # Convert to dictionary format
    metadata_dict = {entry.field: entry.value for entry in metadata_entries}
    
    return MetadataFormatted(data=metadata_dict)

# TODO: implement password protection for this route.
@app.get(
    "/v1/admin/refreshInternals",
    summary="Refreshes the internals",
    description="Reloads the database from disk and clears the cache. Not for public use.",
    include_in_schema=False
)
async def refreshInternals(
    *,
    session: Session = Depends(get_session),
):  
    fetchDB()
    await FastAPICache.clear()


@app.get("/v1/admin/check_cache", include_in_schema=False)
async def check_cache():
    return FastAPICache.get_backend()._store

@app.get("/v1/admin/clear_cache", include_in_schema=False)
async def clear_cache():
    FastAPICache.clear()
