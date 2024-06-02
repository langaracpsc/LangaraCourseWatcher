from seleniumwire import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time
import re
import requests
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

def get_wp_nonce_selenium_wire(url='https://www.bctransferguide.ca/transfer-options/search-courses/') -> str | None:
    # Setup Chrome options for headless mode
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    # Initialize the WebDriver using ChromeDriverManager
    driver = webdriver.Chrome(
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

# Example usage
nonce = get_wp_nonce_selenium_wire()

print(nonce)