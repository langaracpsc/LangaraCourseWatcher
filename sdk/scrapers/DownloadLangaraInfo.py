import concurrent.futures
import logging
from concurrent.futures import Future
from typing import TYPE_CHECKING

import requests
import requests_cache
from bs4 import BeautifulSoup

from sdk.scrapers.ScraperUtilities import createSession

logger = logging.getLogger("LangaraCourseWatcherScraper")


if TYPE_CHECKING:
    from api import CACHE_DB_LOCATION


def getSubjectsFromWeb(year: int, semester: int, use_cache=False) -> list | None:
    # get available subjects (ie ABST, ANTH, APPL, etc)
    url = f"https://swing.langara.bc.ca/prod/hzgkfcls.P_Sel_Crse_Search?term={year}{semester}"

    session = createSession("database/cache/cache.db", use_cache)
    i = session.post(url)

    # TODO: optimize finding this list
    soup = BeautifulSoup(i.text, "lxml")
    courses = soup.find("select", {"id": "subj_id"})
    courses = courses.findChildren()
    subjects = []
    for c in courses:  # c = ['<option value=', 'SPAN', '>Spanish</option>']
        subjects.append(str(c).split('"')[1])

    if len(subjects) == 0:
        # logger.info(f"No sections found for {year}{semester}.")
        return None

    return subjects


def fetchTermFromWeb(
    year: int,
    term: int,
    use_cache=False,
    subjects_override: list[str] = None,
) -> tuple[str, str, str] | None:
    logger.info(f"{year}{term} : Downloading data.")

    if subjects_override == None:
        subjects = getSubjectsFromWeb(year, term, use_cache)

        if subjects == None:
            if use_cache:
                logger.info(f"{year}{term} : No subjects found.")
            else:
                logger.info(
                    f"{year}{term} : No subjects found (note that this request was made to the cache.)."
                )
            return None

    subjects_data = ""
    for s in subjects:
        subjects_data += f"&sel_subj={s}"

    session = createSession("database/cache/cache.db", use_cache)

    url = "https://swing.langara.bc.ca/prod/hzgkfcls.P_GetCrse"
    headers = {"Content-type": "application/x-www-form-urlencoded"}

    data = f"term_in={year}{term}&sel_subj=dummy&sel_day=dummy&sel_schd=dummy&sel_insm=dummy&sel_camp=dummy&sel_levl=dummy&sel_sess=dummy&sel_instr=dummy&sel_ptrm=dummy&sel_attr=dummy&sel_dept=dummy{subjects_data}&sel_crse=&sel_title=%25&sel_dept=%25&begin_hh=0&begin_mi=0&begin_ap=a&end_hh=0&end_mi=0&end_ap=a&sel_incl_restr=Y&sel_incl_preq=Y&SUB_BTN=Get+Courses"
    sections = session.post(url, headers=headers, data=data)

    url = f"https://swing.langara.bc.ca/prod/hzgkcald.P_DisplayCatalog?term_in={year}{term}"
    catalogue = session.post(url)

    url = (
        f"https://swing.langara.bc.ca/prod/hzgkcald.P_DispCrseAttr?term_in={year}{term}"
    )
    attributes = session.post(url)

    return (sections.text, catalogue.text, attributes.text)


# uses multiple threads for increased speed: https://stackoverflow.com/a/68583332/5994461
# may get rid of the function in method declaration later
def DownloadAllTermsFromWeb(
    function, multithread=True, max_threads=3 * 8
) -> list[tuple[int, int, str]]:
    HTML = []
    year = 1999  # this is the furthest back the SIS has records for.
    term = 20

    pool = concurrent.futures.ThreadPoolExecutor()
    if multithread == False:
        max_threads = 1
    pool._max_workers = max_threads  # Don't DDOS Langara
    futures: list[Future] = []

    with pool as executor:
        while True:
            # not multi threaded because it is pretty cheap
            subjects = getSubjectsFromWeb(year, term)

            if subjects == None:
                logger.info(f"{year}{term}: No data found. Subject search is complete.")
                break

            future = executor.submit(fetchTermFromWeb, year, term, subjects)
            futures.append(future)

            if term == 10:
                term = 20
            elif term == 20:
                term = 30
            elif term == 30:
                term = 10
                year += 1

            def retrieveDownloads(futures: list[Future], arr: list, function):
                for f in reversed(futures):
                    if f.done():
                        r = f.result()

                        function(r[0], r[1], r[2], r[3], r[4])
                        arr.append((r[0], r[1], r[2], r[3], r[4]))
                        logger.info(f"{r[0]}{r[1]} : HTML downloaded.")

                        futures.remove(f)

            retrieveDownloads(futures, HTML, function)

        while True:
            # wait for all HTML requests to finish
            tup = concurrent.futures.wait(futures, timeout=1)

            # Do one final retrieval
            retrieveDownloads(futures, HTML, function)

            # tup contains 2 sets - done & not_done - once not_done is empty we can exit
            if len(tup[1]) == 0:
                break

    return HTML
