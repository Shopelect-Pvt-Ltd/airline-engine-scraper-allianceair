import logging
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from PIL import Image
from io import BytesIO
import base64
from webdriver_manager.chrome import ChromeDriverManager
import utils.captcha as captcha
import os
from utils import s3


def create_web_driver():
    options = webdriver.ChromeOptions()
    prefs = {
        "download.default_directory": os.path.join(os.getcwd(), "temp"),
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False,
        "directory_upgrade": True
    }
    options.add_experimental_option("prefs", prefs)
    options.add_experimental_option("excludeSwitches", ['enable-automation'])
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--window-size=1920,1400")
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--headless")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.implicitly_wait(1)
    return driver


def attempt_login(driver, date, pnr, airline):
    try:
        url = 'https://allianceair.co.in/gst/'
        driver.get(url)
        time.sleep(5)

        driver.find_element(By.ID, "txtDOJ").click()
        driver.find_element(By.ID, "txtDOJ").clear()
        driver.find_element(By.ID, "txtDOJ").send_keys(date)
        time.sleep(3)
        driver.find_element(By.ID, "txtPNR").click()
        driver.find_element(By.ID, "txtPNR").clear()
        driver.find_element(By.ID, "txtPNR").send_keys(pnr)
        time.sleep(3)

        captcha_image_element = driver.find_element(By.ID, "Image1")
        captcha_image_data = captcha_image_element.screenshot_as_png

        image = Image.open(BytesIO(captcha_image_data))
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        base64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")

        captcha_id, captcha_text = captcha.get_captcha_base64(base64_image)
        print("CaptchaEarlier----------", captcha_text)
        time.sleep(2)
        captcha_text_cap = captcha_text.upper()
        print("Captcha----------", captcha_text_cap)

        driver.find_element(By.ID, "txtVerificationCodeNew").click()
        driver.find_element(By.ID, "txtVerificationCodeNew").clear()
        driver.find_element(By.ID, "txtVerificationCodeNew").send_keys(captcha_text)
        button = driver.find_element(By.XPATH, f'//*[@id="btnSearch"]')
        button.click()
        time.sleep(5)
        try:
            driver.find_element(By.ID, "lnkdownload").click()
            filename = driver.find_element(By.XPATH, '//*[@id="lbl"]').text
            if filename:
                print("Files downloaded")
                filepath = os.path.join(os.getcwd(), "temp") + "/" + filename + ".pdf"
                pdf_status, pdf_s3link = s3.upload_s3(filepath, filename + ".pdf", airline)
                logging.info("File Uploaded to S3")
                if os.path.exists(filepath):
                    os.remove(filepath)
                    logging.info(f"{filepath} has been deleted.")
                else:
                    logging.info(f"{filepath} does not exist.")
                return True, pdf_status
            else:
                return False, None

        except Exception as e:
            print("Files not downloaded:", e)
            return False, None

    except Exception as e:
        print("Error during login or form submission:", e)
        return False, None


def alliance_scraper(data):
    max_attempts = 3
    try:
        vendor = data['Vendor']
        airline = 'alliance'
        if vendor is None and vendor == 'ALLIANCE AIR':
            airline = 'alliance'
        pnr = data['Ticket/PNR']
        date = data['Transaction_Date']
        success = False
        for attempt in range(max_attempts):
            driver = create_web_driver()
            status, pdf_s3link = attempt_login(driver, date, pnr, airline)
            if status:
                success = True
                return {
                    "success": True,
                    "message": "FILE_PUSHED_TO_S3",
                    "data": {'s3_link': [pdf_s3link], 'airline': airline}
                }

            else:
                print(f"Attempt {attempt + 1} failed for PNR: {pnr}. Retrying...")

            driver.quit()  # Ensure the browser is closed before retrying
        if not success:
            print(f"Failed to download files after {max_attempts} attempts for PNR: {pnr}")
            return {
                "success": False,
                "message": "ERROR_PROCESSING",
                "data": {}
            }
    except Exception as e:
        print("Error in alliance_scraper function:", e)
        return {
            "success": False,
            "message": "ERROR_PROCESSING",
            "data": {}
        }
