import datetime
import logging
import unicodedata

import cchardet
import lxml
from bs4 import BeautifulSoup

from sdk.schema.sources.ScheduleEntry import ScheduleEntryDB
from sdk.schema.sources.Section import SectionDB

logger = logging.getLogger("LangaraCourseWatcherScraper")

"""
Parses a page and returns all of the information contained therein.

Naturally there are a few caveats:
1) If they ever change the course search interface, this will break horribly
2) For a few years, they had a course-code note that applied to all sections of a course.
    Instead of storing that properly, we simply append that note to the end of all sections of a course.

"""


# TODO: refactor this method to make it quicker
def parseSemesterHTML(html: str) -> tuple[list[SectionDB], list[ScheduleEntryDB]]:
    # use BeautifulSoup to change html to Python friendly format
    soup = BeautifulSoup(html, "lxml")

    # "Course Search For Spring 2023" is the only h2 on the page
    title = soup.find("h2").text.split()
    year = int(title[-1])
    if "Spring" in title:
        term = 10
    if "Summer" in title:
        term = 20
    if "Fall" in title:
        term = 30

    sections = []
    schedules = []
    # print(f"{year}{term} : Beginning parsing.")

    # Begin parsing HTML
    table1 = soup.find("table", class_="dataentrytable")

    # do not parse information we do not need (headers, lines and course headings)
    rawdata: list[str] = []
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
        if len(txt) == 9 and txt[0:4].isalpha() and txt[5:9].isnumeric():
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

    while i < len(rawdata) - 1:
        # some class-wide notes that apply to all sections of a course are put in front of the course (see 10439 in 201110)
        # this is a bad way to deal with them
        if len(rawdata[i]) > 2:
            # 0 stores the subj and course id (ie CPSC 1150)
            # 1 stores the note and edits it properly
            sectionNotes = [rawdata[i][0:9], rawdata[i][10:].strip()]
            # print("NEW SECTIONNOTES:", sectionNotes)
            i += 1

        # terrible way to fix off by one error (see 30566 in 201530)
        if rawdata[i].isdigit():
            i -= 1

        fee: str = formatProp(rawdata[i + 10])
        # required to convert "$5,933.55" -> 5933.55
        if fee != None:
            fee = fee.replace("$", "")
            fee = fee.replace(",", "")
            fee = float(fee)

        rpt = formatProp(rawdata[i + 11])
        if rpt == "-":
            rpt = None

        subject = rawdata[i + 5]
        course_code = rawdata[i + 6]
        crn = formatProp(rawdata[i + 4])

        # idek anymore don't code at 2 am
        rp = formatProp(rawdata[i])
        if rp != None:
            rp = "".join(rp.split())
            rp = formatProp(rp)

        current_course = SectionDB(
            # SECT-subj-code-year-term-crn
            # SECT-ENGL-1123-2024-30-31005
            id=f"SECT-{subject}-{course_code}-{year}-{term}-{crn}",
            RP=rp,
            seats=rawdata[i + 1],
            waitlist=rawdata[i + 2],
            # skip the select column
            crn=crn,
            section=rawdata[i + 7],
            credits=formatProp(rawdata[i + 8]),
            abbreviated_title=rawdata[i + 9],
            add_fees=fee,
            rpt_limit=rpt,
            notes=None,
            id_course=f"CRSE-{subject}-{course_code}",
            id_semester=f"SMTR-{year}-{term}",
            # id_course_max=f'CMAX-{subject}-{course_code}',
            subject=subject,
            course_code=course_code,
            year=year,
            term=term,
        )

        if sectionNotes != None:
            if (
                sectionNotes[0]
                == f"{current_course.subject} {current_course.course_code}"
            ):
                current_course.notes = sectionNotes[1]
            else:
                sectionNotes = None

        sections.append(current_course)
        i += 12

        schedule_count = 0

        while True:
            # sanity check
            if rawdata[i] not in [
                " ",
                "CO-OP(on site work experience)",
                "Lecture",
                "Lab",
                "Seminar",
                "Practicum",
                "WWW",
                "On Site Work",
                "Exchange-International",
                "Tutorial",
                "Exam",
                "Field School",
                "Flexible Assessment",
                "GIS Guided Independent Study",
            ]:
                raise Exception(
                    f"Parsing error: unexpected course type found: {rawdata[i]}. {current_course} in course {current_course.toJSON()}"
                )

            c = ScheduleEntryDB(
                # SCHD-subj-code-year-term-crn-section_number
                # SCHD-ENGL-1123-2024-30-31005-1
                id=f"SCHD-{subject}-{course_code}-{year}-{term}-{crn}-{schedule_count}",
                subject=subject,
                course_code=course_code,
                year=year,
                term=term,
                crn=current_course.crn,
                type=rawdata[i],
                days=rawdata[i + 1],
                time=rawdata[i + 2],
                start=formatDate(rawdata[i + 3], year),
                end=formatDate(rawdata[i + 4], year),
                room=rawdata[i + 5],
                instructor=rawdata[i + 6],
                id_course=f"CRSE-{subject}-{course_code}",
                id_semester=f"SMTR-{year}-{term}",
                id_section=f"SECT-{subject}-{course_code}-{year}-{term}-{crn}",
            )
            schedule_count += 1

            if c.start.isspace():
                c.start = None
            if c.end.isspace():
                c.end = None

            schedules.append(c)
            i += 7

            # if last item in courselist has no note return
            if i > len(rawdata) - 1:
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
                    current_course.notes = (
                        rawdata[i].replace("\n", "").replace("\r", "")
                    )  # dont save newlines
                else:
                    current_course.notes = (
                        rawdata[i].replace("\n", "").replace("\r", "")
                        + "\n"
                        + current_course.notes
                    )
                i += 5
                break

            # otherwise, its the same section but a second time
            if j == 12:
                continue

            else:
                break

    return (sections, schedules)


# formats inputs for course entries
# this should be turned into a lambda
def formatProp(s: str) -> str | int | float:
    if s.isspace():
        return None
    if s.replace(".", "", 1).isdigit() and "." in s:
        return float(s)
    if s.isdecimal():
        return int(s)
    else:
        return s.strip()


# converts date from "11-Apr-23" to "2023-04-11" (ISO 8601)
def formatDate(date: str, year: int) -> datetime.date:
    if date == None:
        return None

    if len(date) != 9 or len(date.split("-")) != 3 or date.split("-")[1].isdigit():
        return date

    date = date.split("-")
    months = [
        "jan",
        "feb",
        "mar",
        "apr",
        "may",
        "jun",
        "jul",
        "aug",
        "sep",
        "oct",
        "nov",
        "dec",
    ]

    month = months.index(date[1].lower()) + 1
    if month <= 9:
        month = "0" + str(month)

    # oh no, this will break when 2100 comes around!
    if year <= 1999:
        out = f"19{date[2]}-{month}-{date[0]}"
    else:
        out = f"20{date[2]}-{month}-{date[0]}"
    return out
