import sys
import zlib
from selenium import webdriver
from selenium.common.exceptions import NoSuchWindowException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.firefox.options import Options

import os
import fitz

import concurrent.futures
from concurrent.futures import Future

from urllib3 import HTTPConnectionPool

#from LangaraCourseInfo import Database

"""
Class for scraping information from the BC Transfer Guide
fetch_new_data will download pdfs to the local /downloads folder then archive them in the sql database
You should call this function in its own thread because even with multithreading, it takes ~30 minutes for selenium
to scrape all 136 subjects.
"""

class TransferScraperManager:

    # YOU SHOULD CALL THIS
    def fetch_new_data(db):
        
        #assert isinstance(db, Database) # Doesn't work because of circular import
        
        TransferScraperManager.DownloadAllTransfersFromWeb()
        TransferScraperManager.sendPDFToDatabase(db)


    # uses multiple threads for increased speed: https://stackoverflow.com/a/68583332/5994461 
    def DownloadAllTransfersFromWeb(multithread=True, max_threads=5) -> None:
        
        HEADLESS = True
        
        pool = concurrent.futures.ThreadPoolExecutor()
        if multithread == False:
            max_threads = 1
        pool._max_workers = max_threads # Don't DDOS Langara
        futures:list[Future] = []
        
        print(f"Launching initial Selenium instance... ")
        initial_instance = TransferScraper(headless=HEADLESS, thread_num=1)
    
        print("Retrieving available subjects.")
        subjects = initial_instance.generate_subjects()
        print(f"Found transfer information for {len(subjects)} subjects.")
        subject_count = len(subjects)
        
        assert subject_count > 1, f"Subject count is too low. {subjects}"
        assert subject_count < 500, f"Subject count is too high. {subjects}"
        
        # Load instances
        
        selenium_instances:list[TransferScraper] = [initial_instance]
        for i in range(1, max_threads):
            print(f"Launching Selenium... ({i+1}/{max_threads})")
            selenium_instances.append(TransferScraper(headless=HEADLESS, thread_num=i+1))
        
        # Begin threaded execution
        
        with pool as executor:
            
            def create_selenium_thread():
                future = executor.submit(instance.downloadSubjects, subjects, subject_count)
                futures.append(future)
            
            for instance in selenium_instances:
                create_selenium_thread()
            
                
        # wait for all HTML requests to finish
        while True:
            tup = concurrent.futures.wait(futures, timeout=1)
            
            for f in reversed(futures):
                
                if f.exception():
                    futures.remove(f)
                    print("Exception:", f.exception)    
                
                elif f.done():
                    futures.remove(f)
                
            
            if len(futures) == 0:
                break
        
        if (len(subjects) > 0):
            raise Exception(f"Not all subjects were parsed. {len(subjects)} remaining. ({subjects})")
        
        print("Transfer fetching complete.")
        
    
            
    # Sends PDFs in /downloads to the database then deletes them
    def sendPDFToDatabase(database, path="downloads/", delete = True):
        dir = path
        pdfs = os.listdir(dir)
                        
        for i, p in enumerate(pdfs):
            
            # parse some information about the pdf
            with fitz.open(dir+p) as pdf:
                text = chr(12).join([page.get_text() for page in pdf])
            
            info = text[0:100].split()
            subject = info[5]
            agreements = info[7]
            courses = info[11]
            institutions = info[14]
                        
            # actually save the pdf
            with open(dir+p, "rb") as fi:
                database.insertTransferPDF(subject, zlib.compress(fi.read()))
                
            #print(f"Inserted transfer agreements for {subject} into the database ({i+1}/{len(pdfs)}).")
        
        print(f"Inserted {len(pdfs)} PDFs into the database.")
        
        if delete:
            for p in pdfs:
                os.remove(dir+p)       
    
    # Extracts pdfs from database and returns them to file format
    def retrieveAllPDFFromDatabase(database, path="downloads/"):
        dir = path
        
        # don't overwrite files
        # assert len(os.listdir(dir)) == 0, f"Empty {dir} before retrieving PDFs!"
    
        pdfs = database.getAllTransferPDF()
                
        for p in pdfs:
            
            subj = "".join(x for x in p[0] if x.isalnum()) # sanitize
            filename = f"{dir}{subj} Transfer Information.pdf"
            
            with open(filename, "wb") as fi:
                try:
                    fi.write(zlib.decompress(p[1]))
                except:
                    fi.write(p[1])
                        
        
        
class TransferScraper:
    def __init__(self, institution = "LANG", delay = 0.3, headless = True, thread_num=None) -> None:
        
        self.thread_num = thread_num
        
        options = Options()
        if headless == True:
            options.add_argument("--headless")
        # download files to \downloads
        options.set_preference("browser.download.folderList", 2)
        options.set_preference("browser.download.manager.showWhenStarting", False)
        options.set_preference('browser.download.dir', f"{os.path.abspath(os.getcwd())}\downloads")
        
        options.set_preference("browser.cache.disk.enable", False)
        options.set_preference("browser.cache.memory.enable", False)
        options.set_preference("browser.cache.offline.enable", False)
        options.set_preference("network.http.use-cache", False)
        
        options.set_preference("permissions.default.stylesheet", 2)
        options.set_preference("permissions.default.image", 2)


        driver = webdriver.Firefox(options=options)
        driver.implicitly_wait(10)
        driver.set_window_size(200, 800)
        driver.execute_script("document.body.style.zoom = '50%'")

        self.driver = driver
        self.d:int = delay
        self.actions = ActionChains(driver)
        
        self.institution = institution
        self.subjects:list[tuple[str, str]] = []
        
        
        
        
    # Go back to starting page and set institution.
    def initialize(self):
        
        link = "https://www.bctransferguide.ca/transfer-options/search-courses/"
        
        self.driver.switch_to.new_window('tab')
        old = self.driver.window_handles[0]
        new = self.driver.window_handles[1]
        self.driver.switch_to.window(old)
        self.driver.close()
        self.driver.switch_to.window(new)
        
        self.driver.get(link)
        
        # scroll down a bit
        self.actions.scroll_by_amount(0, 700).pause(self.d).perform()
        
        # select institution
        wait = WebDriverWait(self.driver, 15)
        institutionEl = wait.until(EC.presence_of_element_located((By.ID, "institutionSelect")))
        
        # TODO: figure out why setting institution breaks sometimes
        self.actions.pause(2).perform()
        self.actions.move_to_element(institutionEl).pause(self.d).click().pause(self.d).send_keys(self.institution).pause(self.d).send_keys(Keys.ENTER).pause(self.d).perform()
        self.actions.pause(2).perform()
        
    def generate_subjects(self) -> list[tuple[str, str]]:
        
        self.initialize()

        subjectsEl = self.driver.find_elements(By.CLASS_NAME, "multiselect__content")
        subjectsHTML = subjectsEl[2].get_attribute('innerHTML')
        splitHTML = subjectsHTML.split('title="')
        
        for i in splitHTML:
            data = i[0:200].split('"')[0]
            
            # ignore first title
            if "<!----> <li class=" in data:
                continue
                
            subj = data.split(" - ")[0]
            if " - " in data:
                desc = data.split(" - ")[1].replace("&amp;", "&").strip()
            else:
                desc = None
            self.subjects.append((subj, desc))
        
        #print(f"Found transfer information for {len(self.subjects)} subjects.")
        return self.subjects
    
    def downloadSubjects(self, subjects_arr:list, subject_count):
        
        KILL_THRESHOLD = 3
        kills = 0
                
        while len(subjects_arr) > 0:
            subject = subjects_arr.pop(0)
            
            
            print(f"Downloading transfer information for {subject[0]} - {subject[1]} ({subject_count-len(subjects_arr)}/{subject_count}) on thread {self.thread_num}.")
            
            self.downloadSubject(subject)
            
            try:
                #self.downloadSubject(subject)
                pass
                
            except Exception as e:
                print(f"Failure to download {subject[0]} - {subject[1]} on thread {self.thread_num}: {e}")
                subjects_arr.insert(0, subject) # try to re scrape subject
                
                kills += 1
                if kills >= KILL_THRESHOLD:
                    print(f"Terminating thread {self.thread_num}.")
                    self.driver.quit()
                    raise e
                
        self.driver.quit()
    
        

    def downloadSubject(self, subject:tuple[str, str]):
                        
        self.initialize()
        de = self.d
        
        subjectEl = self.driver.find_element(By.ID, "subjectSelect")
        courseEl = self.driver.find_element(By.ID, "courseNumber")

        # Select subject from list
        search = subject[0]
        if subject[1] != None:
            search += " - "
        
        self.actions.move_to_element(subjectEl).click().pause(de).send_keys(search).pause(de).perform()
        
        search = subject[0]
        if subject[1] != None:
            search += " - "
            
        wait = WebDriverWait(self.driver, 15)
        wait.until(EC.presence_of_element_located((By.XPATH, f"//*[contains(text(), '{search}')]")))
        subj = self.driver.find_element(By.XPATH, f"//*[contains(text(), '{search}')]")
        self.actions.move_to_element(subj).click().pause(de).perform()
      
        # make request
        self.actions.move_to_element(courseEl).click().pause(de).send_keys(Keys.ENTER).perform()
        
        # wait for request to load
        wait = WebDriverWait(self.driver, 90) 
        wait.until(EC.visibility_of_element_located((By.XPATH, "//*[contains(text(), 'Showing result')]")))

        BAD = False
        
        try:
            no_result = self.driver.find_element(By.XPATH, "//h6[contains(text(), 'There are no transfer agreements')]")
            if no_result and 'Please try again.' in no_result.text:
                BAD = True
        except:
            pass # sorry
            
        if BAD:
            print(f"No transferrable courses for {subject[0]}.")
            return
        
        # TODO: basic diagnostics e.g. how many courses transfer for the subject
        
        # save PDF
        pdfButton = self.driver.find_element(By.XPATH, f"//*[contains(text(), 'Save to PDF')]")
        self.actions.move_to_element(pdfButton).click().perform()
        
        # Wait for new tab to open
        wait = WebDriverWait(self.driver, 90) 
        wait.until(EC.number_of_windows_to_be(2))
        
        parent = self.driver.window_handles[0]
        chld = self.driver.window_handles[1]
        self.driver.switch_to.window(chld)
        
        # genuinely cursed code ahead
        try:
            wait = WebDriverWait(self.driver, 90)
            wait.until(EC.title_contains("course"))
        
            raise Exception(f"PDF for {subject[0]} did not download in 90 seconds.")
        except NoSuchWindowException:
            print(f"PDF downloaded for {subject[0]}.")
            # close pdf window and navigate back to transfer search
            wait = WebDriverWait(self.driver, 10) 
            wait.until(EC.number_of_windows_to_be(2))
            
            pdf = self.driver.window_handles[1]
            self.driver.switch_to.window(pdf)
            self.driver.close()
            self.driver.switch_to.window(parent)