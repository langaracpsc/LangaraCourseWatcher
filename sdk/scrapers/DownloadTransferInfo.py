
from concurrent.futures import ThreadPoolExecutor
import json

from requests import Session
from requests_cache import CachedSession, Optional
from sqlmodel import Field, SQLModel
from sdk.schema.sources.Transfer import Transfer, TransferDB
from sdk.scrapers.ScraperUtilities import createSession

import logging
import os


import time
import re

import asyncio
import re
from playwright.async_api import async_playwright

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from api import CACHE_DB_LOCATION
    

import logging
logger = logging.getLogger("LangaraCourseWatcherScraper") 


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
    
    logger.info(f"{institution} {subject.subject} : Getting transfers.")
        
    pages = []
    
    data = _getSubjectPage(subject, 1, session, use_cache, wp_nonce, institution, institution_id)
    page = parsePageRequest(data)
    
    pages = [page]
    
    logger.info(f"{institution} {subject.subject} : {page.total_agreements} transfer agreements available ({page.total_pages} pages).")
    
    if page.total_pages > 1:
        for page_num in range(2, page.total_pages+1): # pages start at 1, not 0          
            data = _getSubjectPage(subject, page_num, session, use_cache, wp_nonce, institution, institution_id)
            page = parsePageRequest(data, page.current_subject, page.current_course_code, page.current_i)
            pages.append(page)
            
            if page.current_page % 10 == 0:
                logger.info(f"{institution} {subject.subject} : Downloaded {page.current_page}/{page.total_pages} transfer pages.")
    
    # generate output
    transfers:list[TransferDB] = []
    for p in pages:
        transfers.extend(p.transfers)
    
    logger.info(f"{institution} {subject.subject} : {len(transfers)} transfer agreements found.")    
    
    # logger.info(transfers)
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
    current_course_code: Optional[str]
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
            course_code = t["SndrCourseNumber"]
            
            if subject != r.current_subject or course_code != r.current_course_code:
                r.current_subject = subject
                r.current_course_code = course_code
                r.current_i = 0
            
            
            transfer = TransferDB(
                
                # TRAN-ENGL-1123-UBCV-309967
                id = f'TRAN-{subject}-{course_code}-{t["Id"]}',
                
                transfer_guide_id=t["Id"],
                
                source_credits = t["SndrCourseCredit"],
                source_title = t["SndrCourseTitle"],
                
                source= t["SndrInstitutionCode"],
                # source_name = t["SndrInstitutionName"],
                destination = t["RcvrInstitutionCode"],
                destination_name = t["RcvrInstitutionName"],
                
                credit = t["Detail"],
                condition = t["Condition"],
                
                effective_start= t["StartDate"],
                effective_end = t["EndDate"],
                
                subject = subject,
                course_code = course_code,
                
                id_course=f'CRSE-{subject}-{course_code}',
                # id_course_max=f'CMAX-{subject}-{course_code}'
            )
            
            r.current_i += 1
            r.transfers.append(transfer)
    
    return r

def getTransferInformation(use_cache:bool, institution="LANG", institution_id:int=15) -> list[TransferDB]:
    
    session = createSession("database/cache/cache.db", use_cache=use_cache)

    subjects = getSubjectList(session, use_cache=use_cache)
    
    transfers:list[TransferDB] = []
    
    # there's really no caching this
    logger.info("Getting wp_nonce...")
    # taken from stackoverflow
    # neccessary because sometimes we call this function from the api
    # and sometimes we want to call it manually
    # and there can only be one asyncio loop at a time
    try:
        asyncio.get_running_loop() # Triggers RuntimeError if no running event loop
        # Create a separate thread so we can block before returning
        with ThreadPoolExecutor(1) as pool:
            wp_nonce = pool.submit(lambda: asyncio.run(getWPNonce(use_cache))).result()
    except RuntimeError:
        wp_nonce = asyncio.run(getWPNonce(use_cache))
        
    assert wp_nonce != None
    logger.info(f"Found wp_nonce: {wp_nonce}")
    
    for s in subjects:
        t = getSubject(s, session, use_cache=use_cache, wp_nonce=wp_nonce)
        transfers.extend(t)
    
    return transfers

# WOW THAT WAS PAINFUL
async def getWPNonce(use_cache: bool=False, url='https://www.bctransferguide.ca/transfer-options/search-courses/') -> str | None:
    # this breaks on a clean run of the code
    # if use_cache:
    #     return "CACHE_NONCE"
    
    nonce_container = {'nonce': None}
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        await page.goto(url)
        
        # this is a product of chatgpt
        page.on('request', lambda request: (
            re.search(r'_wpnonce=([a-zA-Z0-9]+)', request.url) and
            nonce_container.update({'nonce': re.search(r'_wpnonce=([a-zA-Z0-9]+)', request.url).group(1)})
        ))

        # Select institution
        await page.click('label[for="institutionSelect"]')
        await page.type("#institutionSelect", "LANG")
        await page.press("#institutionSelect", "Enter")

        search = "ABST"
        await page.click('label[for="subjectSelect"]')
        await page.wait_for_timeout(200)
        await page.type("#subjectSelect", search)
        await page.keyboard.down("Enter")
        
        await page.keyboard.down("Tab")
        await page.keyboard.down("Enter")
        
        # wait until the nonce request is sent and the next page starts loading
        await page.wait_for_url("https://www.bctransferguide.ca/transfer-options/search-courses/search-course-result/")
        
        await page.wait_for_load_state()
        
        if nonce_container['nonce'] == None:
            await page.wait_for_timeout(5000)        
        
        await browser.close()

    return nonce_container['nonce']

# # Run the function
# nonce = asyncio.run(getWPNonce())
# logger.info(nonce)



# if __name__ == "__main__":
#     transfers = getTransferInformation(use_cache=True)