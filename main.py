import boto3
import os
import json
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import logging

from scrapers.alliance import alliance_scraper

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
aws_access_key_id=os.getenv('AWS_ACCESS')
aws_secret_access_key=os.getenv('AWS_SECRET')
region_name='ap-south-1'

sqs_client = boto3.client('sqs', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key, region_name=region_name)
queue_url = os.getenv('AIRLINE_ENGINE_SCRAPER_INPUT_ALLIANCEAIR_Q')
engine_update_queue_url = os.getenv('AIRLINE_ENGINE_SCRAPER_OUTPUT_Q')
max_messages = 10
max_workers = 5

def process_each_message(message):
    try:
        logging.info(message)
        scraping_data = json.loads(message['Body'])
        guid = scraping_data['guid']
        data = scraping_data['data']
        scraper = alliance_scraper
        if scraper:
            response = scraper(data)
            response['guid'] = guid
            sqs_client.send_message(
                QueueUrl=engine_update_queue_url,
                MessageBody=json.dumps(response)
            )
    except Exception as e:
        message = {
            "guid": guid,
            "success": False,
            "message": f"ERROR_INVOICE",
            "data": {}
        }
        sqs_client.send_message(
            QueueUrl=engine_update_queue_url,
            MessageBody=json.dumps(message)
        )
        logging.error(f"Error processing message for GUID: {guid}. Error: {str(e)}")


def delete_messages(messages):
    for message in messages:
        receipt_handle = message['ReceiptHandle']
        sqs_client.delete_message(
            QueueUrl=queue_url, ReceiptHandle=receipt_handle)


def process_messages(messages):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for message in messages:
            futures.append(executor.submit(process_each_message, message))
        for future in futures:
            future.result()


while True:
    logging.info("Fetching Messages!! ---- " + datetime.now().strftime('%d-%m-%y %H:%M:%S'))
    try:
        # Receive messages from SQS
        response = sqs_client.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=max_messages,
            VisibilityTimeout=10,
            WaitTimeSeconds=0
        )

        # Process each message
        messages = response.get('Messages', [])
        delete_messages(messages)
        process_messages(messages)
    except Exception as e:
        logging.error(f"Error receiving messages from SQS: {str(e)}")