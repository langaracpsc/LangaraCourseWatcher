from bs4 import BeautifulSoup

import unicodedata
import datetime

from schema.Semester import Course, ScheduleEntry, Semester



'''
Parses the Langara Course Search into json

this classname is very deceptive: This class has methods for
- fetching course pages from the internet
- downloading course pages
- parsing course page

TODO: speed it up - it takes 3 mins to download and parse all 20 years of data :sob:
'''

class SemesterParser:
    def __init__(self, year:int, semester:int) -> None:
        
        if year < 2000:
            raise Exception("Course data is not available prior to 2000.")
        if semester not in [10, 20, 30]:
            raise Exception(f"Invalid semester {semester}. Semester must be 10, 20 or 30.")
        
        self.year = year 
        self.semester = semester
        
        self.courses_first_day = None
        self.courses_last_day = None   
                
        
        
    
"""
Parses a page and returns all of the information contained therein.

Naturally there are a few caveats"
1) If they ever change the course search interface, this will break horribly
2) For a few years, they had a course-code note that applied to all sections of a course.
    Instead of storing that properly, we simply append that note to the end of all sections of a course.

"""
# TODO: refactor this method to make it quicker
def parseSemesterHTML(html) -> Semester:
    courses_first_day = None
    courses_last_day = None
            
    # use BeautifulSoup to change html to Python friendly format
    soup = BeautifulSoup(html, 'lxml')

    # "Course Search For Spring 2023" is the only h2 on the page
    title = soup.find("h2").text.split()
    year = int( title[-1] )
    if "Spring" in title:
        term = 10
    if "Summer" in title:
        term = 20
    if "Fall" in title:
        term = 30
        
    semester = Semester(year=year, term=term)
            
    # Begin parsing HTML 
    table1 = soup.find("table", class_="dataentrytable")

    # do not parse information we do not need (headers, lines and course headings)
    rawdata:list[str] = []
    for i in table1.find_all("td"):
                    
        # remove the grey separator lines
        if "deseparator" in i["class"]: 
            continue
        
        # if a comment is >2 lines, theres whitespace added underneath, this removes them
        if "colspan" in i.attrs and i.attrs["colspan"] == "22":
            continue
        
        # fix unicode encoding
        txt = unicodedata.normalize("NFKD", i.text)
        
        # remove the yellow headers
        if txt == "Instructor(s)":
            rawdata = rawdata[0:-18]
            continue
        
        # remove the header for each course (e.g. CPSC 1150)
        if (len(txt) == 9 and txt[0:4].isalpha() and txt[5:9].isnumeric()):
            continue
        
        # remove non standard header (e.g. BINF 4225 ***NEW COURSE***)
        # TODO: maybe add this to notes at some point?
        if txt[-3:] == "***":
            continue
        
        rawdata.append(txt)

    # Begin parsing data
    # Please note that this is a very cursed and fragile implementation
    # You probably shouldn't touch it
    i = 0
    sectionNotes = None
    courses = []

    while i < len(rawdata)-1:
        
        # some class-wide notes that apply to all sections of a course are put in front of the course (see 10439 in 201110)
        # this is a bad way to deal with them
        if len(rawdata[i]) > 2:
            # 0 stores the subj and course id (ie CPSC 1150)
            # 1 stores the note and edits it properly
            sectionNotes = [
                rawdata[i][0:9],
                rawdata[i][10:].strip()
            ]
            #print("NEW SECTIONNOTES:", sectionNotes)
            i += 1
            
        # terrible way to fix off by one error (see 30566 in 201530)
        if rawdata[i].isdigit():
            i -= 1
        
        fee:str = formatProp(rawdata[i+10])
        # required to convert "$5,933.55" -> 5933.55
        if fee != None:
            fee = fee.replace("$", "")
            fee = fee.replace(",", "")
            fee = float(fee)
        
        rpt = formatProp(rawdata[i+11])
        if rpt == "-":
            rpt = None  
                    
        current_course = Course(
            RP          = formatProp(rawdata[i]),
            seats       = formatProp(rawdata[i+1]),
            waitlist    = formatProp(rawdata[i+2]),
            # skip the select column
            crn         = formatProp(rawdata[i+4]),
            subject     = rawdata[i+5],
            course_code = formatProp(rawdata[i+6]),
            section     = rawdata[i+7],
            credits     = formatProp(rawdata[i+8]),
            title       = rawdata[i+9],
            add_fees    = fee,
            rpt_limit   = rpt,
            
            notes = None,
            schedule = [],
        )
        
        if sectionNotes != None:
            if sectionNotes[0] == f"{current_course.subject} {current_course.course_code}":
                
                current_course.notes = sectionNotes[1]
            else:
                sectionNotes = None
        
        semester.addCourse(current_course)
        i += 12
        
        while True:
            
            # sanity check
            if rawdata[i] not in [" ", "CO-OP(on site work experience)", "Lecture", "Lab", "Seminar", "Practicum","WWW", "On Site Work", "Exchange-International", "Tutorial", "Exam", "Field School", "Flexible Assessment", "GIS Guided Independent Study"]:
                raise Exception(f"Parsing error: unexpected course type found: {rawdata[i]}. {current_course} in course {current_course.toJSON()}")
                                    
            c = ScheduleEntry(
                type       = rawdata[i],
                days       = rawdata[i+1],
                time       = rawdata[i+2], 
                start      = formatDate(rawdata[i+3]), 
                end        = formatDate(rawdata[i+4]), 
                room       = rawdata[i+5], 
                instructor = rawdata[i+6], 
            )
            if c.start.isspace():
                c.start = courses_first_day
            if c.end.isspace():
                c.end = courses_last_day
            
            current_course.schedule.append(c)
            i += 7
            
            # if last item in courselist has no note return
            if i > len(rawdata)-1:
                break
                            
            # look for next item
            j = 0
            while rawdata[i].strip() == "":
                i += 1
                j += 1

            # if j less than 5 its another section
            if j <= 5:
                i -= j 
                break
            
            # if j is 9, its a note e.g. "This section has 2 hours as a WWW component"
            if j == 9:
                # some courses have a section note as well as a normal note
                if current_course.notes == None:
                    current_course.notes = rawdata[i].replace("\n", "").replace("\r", "") # dont save newlines
                else:
                    current_course.notes = rawdata[i].replace("\n", "").replace("\r", "") + "\n" + current_course.notes
                i += 5
                break
            
            # otherwise, its the same section but a second time
            if j == 12:
                continue
            
            else:
                break
    
    return semester

# formats inputs for course entries
# this should be turned into a lambda
def formatProp(s:str) -> str | int | float:
        if s.isdecimal():
            return int(s)
        if s.isspace():
            return None
        else:
            return s.strip()


# converts date from "11-Apr-23" to "2023-04-11" (ISO 8601)
def formatDate(date:str) -> datetime.date:
    if date == None:
        return None
    
    if len(date) != 9 or len(date.split("-")) != 3 or date.split("-")[1].isdigit():
        return date
        
    date = date.split("-")
    months = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
    
    month = months.index(date[1].lower())+1
    if month <= 9:
        month = "0" + str(month)
    
    out = f"20{date[2]}-{month}-{date[0]}"
    return out
    