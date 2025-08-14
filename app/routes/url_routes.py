from bs4 import BeautifulSoup
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import traceback
from selenium.common.exceptions import TimeoutException
from playwright.async_api import async_playwright

router = APIRouter()

# @router.get("/")
# async def root():
#     return {"message": "url routes API"}

from flask import Flask, jsonify


import time


# @router.get("/scrape-tarrant")
# def scrape_tarrant():
#     options = webdriver.ChromeOptions()
#     # options.add_argument("--headless")  # Run in non-headless for testing
#     options.add_argument("--no-sandbox")
#     options.add_argument("--disable-dev-shm-usage")

#     driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

#     try:
#         url = "https://tarrant.tx.publicsearch.us/results?department=RP&keywordSearch=false&recordedDateRange=20250101%2C20250725&searchOcrText=false&searchType=quick"
#         driver.get(url)

#         # Wait until rows are present
#         WebDriverWait(driver, 20).until(
#             EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.result"))
#         )

#         rows = driver.find_elements(By.CSS_SELECTOR, "div.result")
#         results = []

#         for row in rows:
#             try:
#                 grantor = row.find_element(By.XPATH, ".//div[@data-label='Grantor']").text
#                 grantee = row.find_element(By.XPATH, ".//div[@data-label='Grantee']").text
#                 doc_type = row.find_element(By.XPATH, ".//div[@data-label='Doc Type']").text
#                 recorded_date = row.find_element(By.XPATH, ".//div[@data-label='Recorded Date']").text
#                 inst_number = row.find_element(By.XPATH, ".//div[@data-label='Inst Number']").text

#                 results.append({
#                     "grantor": grantor,
#                     "grantee": grantee,
#                     "docType": doc_type,
#                     "recordedDate": recorded_date,
#                     "instNumber": inst_number
#                 })
#             except Exception as e:
#                 print("Row parse failed:", e)
#                 continue

#         return JSONResponse(content=results)
    
#     except Exception as e:
#         return JSONResponse(content={"error": str(e)}, status_code=500)
    
#     finally:
#         driver.quit()

# @router.get("/scrape-tarrant")
# def scrape_tarrant():
#     options = Options()
#     options.add_argument('--headless')
#     options.add_argument('--no-sandbox')
#     options.add_argument('--disable-dev-shm-usage')

#     driver = webdriver.Chrome(options=options)
#     driver.get("https://odyssey.tarrantcounty.com/publicaccess/"
#                 "OdysseyPortal/Home/Dashboard/29")

#     try:
#         wait = WebDriverWait(driver, 60)

#         # Wait for the iframe to load
#         wait.until(EC.presence_of_element_located((By.TAG_NAME, "iframe")))

#         # Switch to iframe
#         iframe = driver.find_element(By.TAG_NAME, "iframe")
#         driver.switch_to.frame(iframe)

#         # Wait for the search input (example: name search box)
#         wait.until(EC.presence_of_element_located((By.ID, "CaseSearchDiv")))

#         # If needed, you can extract or interact here
#         result = driver.page_source

#         return {"status": "success", "message": "Scraped successfully"}

#     except TimeoutException:
#         return JSONResponse(status_code=200, content={
#             "status": "error",
#             "message": "Timeout while waiting for page element"
#         })

#     finally:
#         driver.quit()


# @router.get("/scrape-tarrant")
# async def scrape_tarrant():
#     try:
#         async with async_playwright() as p:
#             browser = await p.chromium.launch(headless=True)
#             page = await browser.new_page()
#             await page.goto("https://odyssey.tarrantcounty.com/publicaccess/")
#             await page.wait_for_timeout(3000)  # Wait for 3 seconds to ensure full load

#             # Get page content
#             content = await page.content()
#             await browser.close()

#             soup = BeautifulSoup(content, "html.parser")

#             # Example: Get only the first record or table row (customize selector as needed)
#             first_record = soup.select_one("table tbody tr")  # Adjust the selector

#             if not first_record:
#                 return {"data": []}

#             data = {
#                 "record_text": first_record.get_text(strip=True),
#                 # add more fields if needed by parsing td tags
#             }

#             return {"data": [data]}

#     except Exception as e:
#         return {"error": str(e)}





@router.get("/scrape-tarrant")
def scrape_tarrant():
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")  # Run in non-headless for testing
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        url = "https://tarrant.tx.publicsearch.us/results?department=RP&keywordSearch=false&recordedDateRange=20250101%2C20250725&searchOcrText=false&searchType=quick"
        driver.get(url)

        # Wait until rows are present
        WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.result"))
        )

        rows = driver.find_elements(By.CSS_SELECTOR, "div.result")
        results = []

        for row in rows:
            try:
                grantor = row.find_element(By.XPATH, ".//div[@data-label='Grantor']").text
                grantee = row.find_element(By.XPATH, ".//div[@data-label='Grantee']").text
                doc_type = row.find_element(By.XPATH, ".//div[@data-label='Doc Type']").text
                recorded_date = row.find_element(By.XPATH, ".//div[@data-label='Recorded Date']").text
                inst_number = row.find_element(By.XPATH, ".//div[@data-label='Inst Number']").text

                results.append({
                    "grantor": grantor,
                    "grantee": grantee,
                    "docType": doc_type,
                    "recordedDate": recorded_date,
                    "instNumber": inst_number
                })
            except Exception as e:
                print("Row parse failed:", e)
                continue

        return JSONResponse(content=results)
    
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
    
    finally:
        driver.quit()