import cchardet
import lxml
from bs4 import BeautifulSoup, element

from sdk.schema.sources.CourseSummary import CourseSummaryDB

"""
Parses the Langara Course Catalogue into json.
https://swing.langara.bc.ca/prod/hzgkcald.P_DisplayCatalog


"""


def parseCatalogueHTML(
    html, year, term, fail_clean=True
) -> list[CourseSummaryDB] | None:
    if not fail_clean:
        return __parseCatalogueHTML(html, year, term)

    try:
        return __parseCatalogueHTML(html, year, term)

    except Exception as e:
        # print("Could not parse catalogue:", e)
        return None


# TODO: This parser has issues and does not work on catalogues before 2012
# probably because catalogues before 2012 have a different format...
def __parseCatalogueHTML(html, year, term) -> list[CourseSummaryDB]:
    if year <= 2011 or (year == 2012 and term == 10):
        return __parseOldCatalogueHTML(html, year, term)

    summaries: list[CourseSummaryDB] = []

    soup = BeautifulSoup(html, "lxml")

    coursedivs: list[element.Tag] = soup.find_all("div", class_="course")

    for div in coursedivs:
        h2 = div.findChild("h2").text
        title = div.findChild("b").text

        # the best way i can find to find an element with no tag
        for e in div.children:
            if not str(e).isspace() and str(e)[0] != "<":
                description = e.text.strip()
                break

        # print(h2)

        h2 = h2.split()
        # h2 = ['ABST', '1100', '(3', 'credits)', '(3:0:0)']
        hours = h2[4].replace("(", "").replace(")", "").split(":")

        subject = h2[0]
        course_code = h2[1]

        c = CourseSummaryDB(
            # CSMR-subj-code-year-term
            # CSMR-ENGL-1123-2024-30
            id=f"CSMR-{subject}-{course_code}-{year}-{term}",
            title=title,
            description=description,
            credits=float(h2[2].replace("(", "")),
            hours_lecture=float(hours[0]),
            hours_seminar=float(hours[1]),
            hours_lab=float(hours[2]),
            subject=subject,
            course_code=course_code,
            year=year,
            term=term,
            id_course=f"CRSE-{subject}-{course_code}",
            id_semester=f"SMTR-{year}-{term}",
        )
        summaries.append(c)

    return summaries


# 2012 10 and OLDER use a different html template
def __parseOldCatalogueHTML(html, year, term) -> list[CourseSummaryDB]:
    summaries: list[CourseSummaryDB] = []

    soup = BeautifulSoup(html, "lxml")

    coursedivs: list[element.Tag] = soup.find_all("div", class_="course")

    for div in coursedivs:
        h2 = div.findChild("h2").text

        title = div.findChild("h1").text

        replacement_course = None
        description = None

        ps = div.find_all("p")
        for p in ps:
            if (
                replacement_course == None
                and "Formerly" in p.text
                or "(Former Title:" in p.text
            ):
                replacement_course = p.text

            elif description == None:
                description = p.text

        # yes, technically this should be a list, I am not making a new table for data from 2011
        requisites = None
        req_texts = div.find_all("p", {"class": "requisite"})
        for r in req_texts:
            if requisites == None:
                requisites = r.text
            else:
                requisites += "\n\n" + r.text

        last_updated = div.findChild("h6").text

        h2 = h2.split()
        # h2 = ['ABST', '1100', '(3', 'credits)', '(3:0:0)']
        hours = h2[4].replace("(", "").replace(")", "").split(":")

        subject = h2[0]
        course_code = h2[1]

        c = CourseSummaryDB(
            # CSMR-subj-code-year-term
            # CSMR-ENGL-1123-2024-30
            id=f"CSMR-{subject}-{course_code}-{year}-{term}",
            title=title,
            description=description,
            desc_replacement_course=replacement_course,
            desc_requisites=requisites,
            desc_last_updated=last_updated,
            credits=float(h2[2].replace("(", "")),
            hours_lecture=float(hours[0]),
            hours_seminar=float(hours[1]),
            hours_lab=float(hours[2]),
            subject=subject,
            course_code=course_code,
            year=year,
            term=term,
            id_course=f"CRSE-{subject}-{course_code}",
            id_semester=f"SMTR-{year}-{term}",
        )
        summaries.append(c)

    return summaries
