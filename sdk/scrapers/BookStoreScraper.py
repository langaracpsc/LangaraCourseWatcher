import logging
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from ScraperUtilities import createSession

URL = "https://mycampusstore.langara.bc.ca/textbook_express/get_txtexpress.asp"
URL2 = "https://mycampusstore.langara.bc.ca/textbook_express.asp"
PARAMS_KEYS = ["dept", "course", "section"]

logger = logging.getLogger("LangaraCourseWatcherScraper")


def get_str_from_tag(tag):
    if not tag:
        return ""
    return tag.text.strip()


class BookStoreScraper:
    def __init__(self, use_cache=False):
        self.session = createSession("database/cache/cache.db", use_cache)

    def extract_courses(self, html):
        """
        Processes HTML data to extract and organize course-related information.

        Args:
            html (str): HTML data containing course information. Usually obtained from `response.text`.

        Returns:
            dict: A structured dictionary containing extracted course book data, formatted as:
                {
                    "DEPT_ID|||COURSE_ID|||SECTION_ID": [
                        {
                            "Course Name": str, # eg. "CPSC - 1480, section M01 (ALL)"
                            "Note": str,
                            "Book List": [
                                {
                                    "cover_img_url": str,
                                    "title": str,
                                    "authors": str,
                                    "isbn": str,
                                    "edition": str,
                                    "binding": str,
                                    "required": bool
                                }
                            ]
                        }
                    ]
                }
        """

        soup = BeautifulSoup(html, "html.parser")
        courses = {}

        book_sections = soup.find("div", attrs={"id": "course-bookdisplay"})
        for course_section in book_sections.find_all("h3"):
            course_name = course_section.find(
                "span", {"id": "course-bookdisplay-coursename"}
            ).text.strip()
            note_section = course_section.find_next("div", class_="course-notes")
            note_text = (
                "\n".join([li.text.strip() for li in note_section.find_all("li")])
                if note_section
                else ""
            )

            # INFO: Making key for courses dict, this key will be easy to parse
            # eg. course_name = "CPSC - 1480, section M01 (ALL)"
            # then course_key will be = "CPSC|||1480|||M01"
            match = re.search(
                r"(\w+)\s+-\s+(\d+),\s+section\s+(\w+)\s+\(\w+\)", course_name
            )
            c_dept, c_course, c_section = match.groups()
            course_key = f"{c_dept}|||{c_course}|||{c_section}"

            courses[course_key] = {
                "Course Name": course_name,
                "Note": note_text,
                "Book List": [],
            }

            table = course_section.find_next("table", class_="data")
            if not table:
                continue

            for row in table.find_all("tr", class_="book-container"):
                cover_td = row.find("td", class_="book-cover")
                cover_img_url = cover_td.a["href"] if cover_td and cover_td.a else ""
                if cover_img_url:
                    cover_img_url = urljoin(URL2, cover_img_url)

                desc_td = row.find("td", class_="book-desc")
                title = get_str_from_tag(desc_td.find("span", class_="book-title"))
                author = get_str_from_tag(desc_td.find("span", class_="book-author"))
                isbn = get_str_from_tag(desc_td.find("span", class_="isbn"))
                edition = get_str_from_tag(desc_td.find("span", class_="book-edition"))
                binding = get_str_from_tag(
                    desc_td.find("span", class_="book-binding")
                ).replace("Binding ", "")
                required = (
                    get_str_from_tag(desc_td.find("p", class_="book-req")).lower()
                    == "required"
                )

                book = {
                    "cover_img_url": cover_img_url,
                    "title": title,
                    "authors": author,
                    "isbn": isbn,
                    "edition": edition,
                    "binding": binding,
                    "required": required,
                }

                courses[course_key]["Book List"].append(book)

        return courses

    def send_second_request(self, first_request_response):
        soup = BeautifulSoup(first_request_response.text, "html.parser")

        form = soup.find("form")

        # INFO: Extract input fields and their values
        # NOTE: Why doing this?
        # Avoid sending POST directly, as the GET response contains dynamic inputs (e.g., XML course list)
        # that may be populated only after loading the page. And XML code format may get changed

        form_data = {}
        for input_tag in form.find_all("input"):
            name = input_tag.get("name")
            value = input_tag.get("value", "")
            if name:
                form_data[name] = value

        return self.session.post(URL2, data=form_data)

    # TODO: make it validate input and give proper output of list of courses book
    def getBooks(self, courses_list: list[dict[str, str]]):
        dept_ids = []
        course_ids = []
        section_ids = []
        for course in courses_list:
            if None in [course.get(k) for k in PARAMS_KEYS]:
                raise ValueError("Invalid course data list")
            dept_ids.append(course["dept"])
            course_ids.append(course["course"])
            section_ids.append(course["section"])

        response0 = self.session.get(
            URL, params={"dept": dept_ids, "course": course_ids, "section": section_ids}
        )
        response = self.send_second_request(response0)

        courses = self.extract_courses(response.text)
        return courses

    def getBook(self, dept: str, course: str, section: str):
        return self.getBooks([{"dept": dept, "course": course, "section": section}])


bookstore_scraper = BookStoreScraper()

if __name__ == "__main__":
    import json

    input_data = [
        {
            "dept": "CPSC",
            "course": "1030",
            "section": "M05",
        },
        {
            "dept": "CPSC",
            "course": "1480",
            "section": "M01",
        },
    ]

    courses = bookstore_scraper.getBooks(input_data)

    print(json.dumps(courses, indent=4))
    print()
    print(
        "===== Above is demo output, it ran and printed out bcz you ran script directly not used this file as module =====".upper()
    )
