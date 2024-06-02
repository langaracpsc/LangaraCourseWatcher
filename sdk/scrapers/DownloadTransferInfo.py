
import json

from requests import Session
from requests_cache import CachedSession, Optional
from sqlmodel import Field, SQLModel
from sdk.schema.Transfer import Transfer, TransferDB
from sdk.scrapers.ScraperUtilities import createSession

import logging
import os

from seleniumwire import webdriver
from selenium.webdriver.common.by import By
import time
import re
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from main import CACHE_DB_LOCATION


headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-CA,en-US;q=0.7,en;q=0.3",
    "Connection": "keep-alive",
    # "Content-Length": "71",
    "Content-Type": "application/x-www-form-urlencoded",
    # "Cookie": "comm100_visitorguid_30000004=43e2385e-2032-4f3a-be6f-f2d2cb239334",
    # "DNT": "1",
    # "Host": "www.bctransferguide.ca",
    # "Origin": "https://www.bctransferguide.ca",
    # "Referer": "https://www.bctransferguide.ca/transfer-options/search-courses/search-course-result/",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    # "Cookie" : "comm100_visitorguid_30000004=43e2385e-2032-4f3a-be6f-f2d2cb239334",
    "Sec-GPC": "1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0"
}

# request_data = {
#     "institutionCode": "LANG",
#     "isPublic": None,
#     "pageNumber" : 1,
#     "sender": 15,
#     "subjectCode": "CPSC",
#     "subjectId": 500,
# }

class TransferSubject(SQLModel):
    # isFPM: bool               # flexible premajor which is apparently no longer a thing
    # UrlFPM: Optional[str]
    # InstitutionID: int      # 15 for langara
    id: int         = Field(description="BCTransfer id of the subject.")
    subject: str    = Field(description="Code of the subject e.g. CPSC, WOMENST")
    title: str      = Field(description="Title of subject e.g. Computer Science, Women's Studies")

def getSubjectList(session: Session | CachedSession, use_cache:bool, institution_id:int=15) -> list[TransferSubject]:
    
    subjects_route = f"https://ws.bctransferguide.ca/api/custom/ui/v1.7/agreementws/GetSubjects?institutionID={institution_id}&sending=true"
    response = session.get(subjects_route, headers=headers)
    result = response.json()
    
    subjects:list[TransferSubject] = []
    
    for r in result:
        s = TransferSubject(
            id=r["Id"],
            subject = r["Code"],
            title = r["Title"]
        )
        subjects.append(s)
        
    return subjects
    

def getSubject(subject:TransferSubject, session: Session | CachedSession, use_cache:bool, wp_nonce:str, institution:str="LANG", institution_id:int=15) -> list[TransferDB]:
    
    print(f"{institution} {subject.subject} : Getting transfers.")
    
    pages = []
    
    data = _getSubjectPage(subject, 1, session, use_cache, wp_nonce, institution, institution_id)
    page = parsePageRequest(data)
    
    pages = [page]
    
    print(f"{institution} {subject.subject} : {page.total_agreements} transfer agreements available ({page.total_pages} pages).")
    
    if page.total_pages > 1:
        for page_num in range(2, page.total_pages+1): # pages start at 1, not 0          
            data = _getSubjectPage(subject, page_num, session, use_cache, wp_nonce, institution, institution_id)
            page = parsePageRequest(data, page.current_subject, page.current_course_code, page.current_i)
            pages.append(page)
            
            if page.current_page % 10 == 0:
                print(f"{institution} {subject.subject} : Downloaded {page.current_page}/{page.total_pages} transfer pages.")
    
    # generate output
    transfers:list[TransferDB] = []
    for p in pages:
        transfers.extend(p.transfers)
    
    print(f"{institution} {subject.subject} : {len(transfers)} transfer agreements found.")    
    
    # print(transfers)
    return transfers

    
def _getSubjectPage(subject:TransferSubject, page:int, session: Session | CachedSession, use_cache:bool, wp_nonce:str, institution:str="LANG", institution_id:int=15) -> dict:
        
    request_data = {
        "institutionCode": institution,
        "isPublic": None,
        "pageNumber" : page,
        "sender": institution_id,
        "subjectCode": subject.title,
        "subjectId": subject.id,
    }
    
    courses_route = f"https://www.bctransferguide.ca/wp-json/bctg-search/course-to-course/search-from?_wpnonce={wp_nonce}"
    # pdf_route = f"https://www.bctransferguide.ca/wp-json/bctg-search/course-to-course/search-from/pdf?_wpnonce={nonce}"
    
    # yes, we have to use post and not get, don't ask me why
    response = session.post(courses_route, data=request_data, headers=headers)
    return response.json()

class PageResponse(SQLModel):
    current_page:int
    total_pages: int
    total_agreements: int
    transfers:list[Transfer] = []
    current_subject: Optional[str]
    current_course_code: Optional[int]
    current_i: int


def parsePageRequest(data:dict, current_subject=None, current_course_code=None, current_i=0) -> PageResponse:
    
    r = PageResponse(
        current_page=data["currentPage"],
        total_pages=data["totalPages"],
        total_agreements=data["totalAgreements"],
        
        current_subject=current_subject,
        current_course_code=current_course_code,
        current_i=current_i
    )
        
    assert "courses" in data
        
    for c in data["courses"]:
                
        for t in c["agreements"]:
            
            subject = t["SndrSubjectCode"]
            course_code = int(t["SndrCourseNumber"])
            
            if subject != r.current_subject or course_code != r.current_course_code:
                r.current_subject = subject
                r.current_course_code = course_code
                r.current_i = 0
            
            
            transfer = TransferDB(
                # TRA-ABST-1100-CAPU-1
                id = f'TRA-{subject}-{course_code}-{r.current_i}',
                course_id=f'CRS-{subject}-{course_code}',
                
                subject = subject,
                course_code = course_code,
                
                source= t["SndrInstitutionCode"],
                # source_name = t["SndrInstitutionName"],
                
                destination = t["RcvrInstitutionCode"],
                # destination_name = t["RcvrInstitutionName"],
                
                credit = t["Detail"],
                condition = t["Condition"],
                
                effective_start= t["StartDate"],
                effective_end = t["EndDate"]
            )
            
            r.current_i += 1
            r.transfers.append(transfer)
    
    return r

def getTransferInformation(use_cache:bool, institution="LANG", institution_id:int=15) -> list[TransferDB]:
    
    session = createSession("database/cache/cache.db", use_cache=use_cache)

    subjects = getSubjectList(session, use_cache=use_cache)
    
    transfers:list[TransferDB] = []
    
    # there's really no caching this
    print("Getting wp_nonce...")
    wp_nonce = getWPNonce()
    
    for s in subjects:
        t = getSubject(s, session, use_cache=use_cache, wp_nonce=wp_nonce)
        transfers.extend(t)
        print()
    
    return transfers

# WOW THAT WAS PAINFUL
def getWPNonce(url='https://www.bctransferguide.ca/transfer-options/search-courses/') -> str | None:
    # from selenium.webdriver.remote.remote_connection import LOGGER
    # LOGGER.setLevel(logging.CRITICAL)
    
    # logger = logging.getLogger('seleniumwire')
    # logger.setLevel(logging.WARNING)
    
    # Setup Chrome options for headless mode
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    options.add_argument('log-level=3')

    # Initialize the WebDriver using ChromeDriverManager
    driver = webdriver.Chrome(
        # service_log_path=os.devnull,
        options=options
    )
    
    driver.get(url)
    
    # Wait for the page to load and the JavaScript to execute
    time.sleep(5)
    
    actions = ActionChains(driver)
    delay = 1
    
    actions.scroll_by_amount(0, 700).pause(5).perform()
        
    # select institution
    wait = WebDriverWait(driver, 15)
    institutionEl = wait.until(EC.presence_of_element_located((By.ID, "institutionSelect")))
    
    # TODO: figure out why setting institution breaks sometimes
    actions.pause(2).perform()
    actions.move_to_element(institutionEl).pause(delay).click().pause(delay).send_keys("LANG").pause(delay).send_keys(Keys.ENTER).pause(delay).perform()
    actions.pause(2).perform()
    
    subjectEl = driver.find_element(By.ID, "subjectSelect")
    courseEl = driver.find_element(By.ID, "courseNumber")

    # Select subject from list
    search = "ABST"
    
    actions.move_to_element(subjectEl).click().pause(delay).send_keys(search).pause(delay).perform()
   
    subj = driver.find_element(By.XPATH, f"//*[contains(text(), '{search}')]")
    actions.move_to_element(subj).click().pause(delay).perform()
    
    # make request
    actions.move_to_element(courseEl).click().pause(delay).send_keys(Keys.ENTER).perform()
    
    
    # Search for nonce in the network requests
    for request in driver.requests:
        if request.response:
            # Search in the request parameters or response body
            if '_wpnonce' in request.url:
                parsed_nonce = re.search(r'_wpnonce=([a-zA-Z0-9]+)', request.url)
                if parsed_nonce:
                    driver.quit()
                    return parsed_nonce.group(1)
            # if request.response.body:
            #     parsed_nonce = re.search(r'_wpnonce=([a-zA-Z0-9]+)', request.response.body.decode('utf-8', errors="ignore"))
            #     if parsed_nonce:
            #         driver.quit()
            #         return parsed_nonce.group(1)
    
    driver.quit()
    return None


# if __name__ == "__main__":
#     transfers = getTransferInformation(use_cache=True)