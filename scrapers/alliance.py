import requests
import json
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from PIL import Image
from io import BytesIO
import base64
import requests
from webdriver_manager.chrome import ChromeDriverManager
import csv
import os
import utils.captcha as captcha
from utils import s3
from utils.log import get_logger
import tempfile

logger = get_logger()

URL = "https://api.airasia.co.in/b2c-gstinvoice/v1/invoice-data/gst"
PDF_URL = "https://api.airasia.co.in/b2c-gstinvoice/v1/invoice-pdf/gst"
HEADERS = {
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
    'Connection': 'keep-alive',
    'Content-Type': 'application/json',
    'Ocp-Apim-Subscription-Key': 'fe65ec9eec2445d9802be1d6c0295158',
    'Origin': 'https://www.airasia.co.in',
    'Referer': 'https://www.airasia.co.in/',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36',
}


def airasia_scraper(data):
    try:
        vendor = data['Vendor']
        airline = 'airasia'
        if vendor == 'Air India Express':
            airline = 'airindiaexpress'
        pnr = data['Ticket/PNR']
        code = data['Origin']
        payload = json.dumps({
            "pnr": pnr,
            "originCode": code
        })
        response = requests.post(URL, headers=HEADERS, data=payload)
        if response.status_code == 200:
            data = response.json()
            for inv in data["data"]["Invoices"]:
                invoice_number = inv.get(
                    "invoiceNumber", inv.get("creditNumber", ""))
                invoice_type = ""
                inv_type = inv.get("type")
                if inv_type == "BOS":
                    invoice_type = "Bill of Supply"
                elif inv_type == "INV":
                    invoice_type = "Tax Invoice"
                elif inv_type == "CR":
                    invoice_type = "Credit Note"

                pdf_payload = json.dumps({
                    "invoiceNumber": invoice_number,
                    "type": inv_type
                })

                response = requests.post(
                    PDF_URL, headers=HEADERS, data=pdf_payload)

                file_name = f'{invoice_number}_{pnr}_{invoice_type}.pdf'

                with tempfile.NamedTemporaryFile(mode='wb') as temp_file:
                    # Write to the temporary file
                    temp_file.write(response.content)


                    pdf_status, pdf_s3link = s3.upload_s3(temp_file.name, file_name, airline)
                    if pdf_status:
                        logger.info("File Uploaded to S3")
                        return {
                            "success": True,
                            "message": "FILE_PUSHED_TO_S3",
                            "data": {'s3_link': [pdf_s3link],'airline':airline}
                        }
                    else:
                        raise Exception("ERROR_FILE_PUSH")
        else:
            raise Exception("ERROR_RESPONSE")
    except Exception as e:
        logger.exception(f"Got an exception {e}")
        return {
            "success": False,
            "message": e.args[0],
            "data": {}
        }