import requests
from bs4 import BeautifulSoup
import lxml
import cchardet

import requests_cache
from sqlmodel import Field, SQLModel

from sdk.schema.CourseOutline import CourseOutlineDB
from sdk.schema.CoursePage import CoursePage, CoursePageDB

from sdk.scrapers.ScraperUtilities import createSession



# from typing import TYPE_CHECKING

# if TYPE_CHECKING:
#     from main import CACHE_DB_LOCATION

class _PageSubject(SQLModel):
    subject_name: str
    subject_code: str
    href : str
    
class _PageCourse(SQLModel):
    subject: str
    course_code: str
    href: str
    
    university_transferable: bool  = Field(description="If the course is university transferrable.")
    offered_online: bool            = Field(description="If there are online offerings for the course.")
    preparatory_course: bool        = Field(description="If the course is prepatory (ie does not offer credits.)")

    
    
    
def getPageSubjectLinks(session) -> list[_PageSubject]:    
    # get links to the course index pages of all subjects
    
    url = f"https://langara.ca/programs-and-courses/courses/index.html"
    
    response = session.get(url)
    
    soup = BeautifulSoup(response.text, features="lxml")
    
    # Find all the <li> tags within the container
    li_tags = soup.select('div.category-column ul.grid li a')

    # Extract course names and URLs
    subjects = []
    for li in li_tags:
        course_name = li.get_text(strip=True)
        course_url = li['href']
        subject_code = course_url.split('/')[0]  # Assuming the subject code is the first part of the URL
        
        course = _PageSubject(
            subject_name=course_name, 
            subject_code=subject_code, 
            href=course_url
        )
        
        subjects.append(course)

    return subjects


def getCoursesFromSubjectPage(
    session: requests_cache.CachedSession | requests.Session, 
    page:_PageSubject
) -> list[_PageCourse]:
        
    courses = []
    
    # Get the page of the subject
    url = f'https://langara.ca/programs-and-courses/courses/{page.href}'
    response = session.get(url)
    soup = BeautifulSoup(response.text, 'lxml')

    # Find all <tr> tags
    tr_tags = soup.find_all('tr')[1:]

    courses = []
    
    for tr in tr_tags:
        
        a_tag = tr.find('a')
        
        # bandaid fixes for bad selecting
        if a_tag == None: 
            continue
        if 'href' not in getattr(a_tag, 'attrs', {}):
            continue
        
        url = a_tag['href'] 
        
        if url == "#":
            continue 
        
        full_code = a_tag.string.strip()
        subject, code = full_code.split()

        # Check glyph statuses
        university_transferable = 'icon-u-transfer-active' in tr.find('span', class_='icon-u-transfer')['class']
        offered_online = 'icon-online-active' in tr.find('span', class_='icon-online')['class']
        preparatory_course = 'icon-preparatory-active' in tr.find('span', class_='icon-preparatory')['class']
    
        course = _PageCourse(
            subject=subject, 
            course_code=code, 
            href=url, 
            
            university_transferable=university_transferable, 
            offered_online=offered_online, 
            preparatory_course=preparatory_course)
        courses.append(course)
    
    return courses
    
def getInformationFromCoursePage(
    session: requests_cache.CachedSession | requests.Session, 
    course:_PageCourse
) -> tuple[CoursePageDB, list[CourseOutlineDB] | None]:
    
    url = f'https://langara.ca{course.href}'
    response = session.get(url)
    soup = BeautifulSoup(response.text, 'lxml')
    
    all_section_inner_divs = soup.find_all('div', class_='section-inner')

    # Iterate through each div and find the one with a child div with class 'section-inner'
    section = None
    for div in all_section_inner_divs:
        if div.find('div', class_='section-inner'):
            section = div
            break
    
    assert section != None
    
    # print(section)
    # input()

    # Extract the course title, subject, and code
    h2_tag = section.find('h2')
    full_title = h2_tag.string.strip()
    subject_code, title = full_title.split(': ', 1)
    subject, course_code = subject_code.split()

    # Extract the course format details
    table = section.find('table', class_='table-course-detail')
    rows = table.find_all('tr')
    hours_lecture, hours_seminar, hours_lab = 0.0, 0.0, 0.0
    credits = 0.0

    for row in rows:
        
        header = row.find('td').string.strip()
        value = row.find_all('td')[1].string.strip()
        
        if header == "Course Format":
            hours_lecture = float(value.split('Lecture ')[1].split(' h')[0])
            hours_seminar = float(value.split('Seminar ')[1].split(' h')[0])
            hours_lab = float(value.split('Lab. ')[1].split(' h')[0])
        elif header == "Credits":
            credits = float(value)
    
    # this breaks sometimes (AHIS 1110), bandaid fix for that
    # if lecture_hours == None:
    #     lecture_hours = 0
    # if seminar_hours == None:
    #     seminar_hours = 0
    # if lab_hours == None:
    #     lab_hours = 0
            
    description = ""
    duplicate_credits = None
    registration_restrictions = None
    prerequisites = None
    replacement_course = None

    # Extract the course description
    if section.find('h3', string='Course Description') == None:
        description_tag = None
    else:
        description_tag = section.find('h3', string='Course Description').find_next('p')

        # coding is painful sometimes
        for content in description_tag:
            if isinstance(content, str):
                if 'Formerly' in content or content.startswith('Discontinued '):
                    replacement_course = content.strip()
                elif 'registration in this course' in content:
                    registration_restrictions = content.strip()
                elif 'receive credit' in content:
                    duplicate_credits = content.strip()
                elif 'Prerequisite(s)' in content:
                    prerequisites = content.strip()
                else:
                    if description != "":
                        description += "\n"
                    description += content.strip()
                
    # Extract course outlines
    outlines = []
    i_outline = 0
    
    outline_section = section.find('h3', text='Course Outline')
    if outline_section:
        ul_tag = outline_section.find_next('ul')
        if ul_tag:
            for li_tag in ul_tag.find_all('li'):
                a_tag = li_tag.find('a')
                if a_tag:
                    
                    link:str = a_tag['href'].strip()
                    link = link.replace("../", "")
                    url=f'https://langara.ca/programs-and-courses/courses/{link}'
                    
                    o = CourseOutlineDB(
                        url=url,
                        file_name=a_tag.text.strip(),
                        
                        # OUTL-ENGL-1123-1
                        id=f'OUTL-{subject}-{course_code}-{i_outline}',
                        
                        subject=subject,
                        course_code=course_code,
                        id_course=f'CRSE-{subject}-{course_code}',
                        id_course_max=f'CMAX-{subject}-{course_code}'
                    )
                    i_outline+=1
                    outlines.append(o)
    
    if outlines == []:
        outlines = None
                    
                    
    # print(description)
    # input()

    c = CoursePageDB(
        # CPGE-ENGL-1123
        id=f'CPGE-{subject}-{course_code}',
        subject=subject,
        course_code=course_code,
        title=title,
        
        credits=credits,
        hours_lecture=hours_lecture,
        hours_seminar=hours_seminar,
        hours_lab=hours_lab,
        
        description=description,
        desc_replacement_course=replacement_course,
        desc_duplicate_credits=duplicate_credits,
        desc_registration_restriction=registration_restrictions,
        desc_prerequisite=prerequisites,
        
        university_transferrable=course.university_transferable,
        offered_online=course.offered_online,
        preparatory_course=course.preparatory_course,
        
        id_course=f'CRSE-{subject}-{course_code}'
    )
    
    return (c, outlines)
    
# THE FUNCTION YOU SHOULD CALL IF YOU WANT COURSE PAGES
def getCoursePageInfo(
    session: requests_cache.CachedSession | requests.Session
) -> tuple[list[CoursePageDB], list[CourseOutlineDB]]:

    subjects = getPageSubjectLinks(session)
    courses:list[CoursePageDB] = []
    outlines: list[CourseOutlineDB] = []

    for s in subjects:
        print(f"{s.subject_code} ({s.subject_name}): Fetching course pages.")

        course_links = getCoursesFromSubjectPage(session, s)
        
        i=0
        for c in course_links:
            c_page, c_outlines = getInformationFromCoursePage(session, c)
            courses.append(c_page)
            if c_outlines != None:
                outlines += c_outlines
            i+=1
        
        print(f"{s.subject_code} ({s.subject_name}): Fetched and parsed {i} courses.")
    
    return (courses, outlines)
            
if __name__ == "__main__":
    session = createSession("database/cache/cache.db", use_cache=True)
    courses, outlines = getCoursePageInfo(session)
