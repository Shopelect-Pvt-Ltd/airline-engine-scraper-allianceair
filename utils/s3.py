from datetime import datetime
import boto3
from botocore.exceptions import NoCredentialsError
from urllib import parse
import os
from dotenv import load_dotenv
from utils.log import get_logger

logger = get_logger()
load_dotenv()

aws_access_key_id=os.getenv('AWS_ACCESS')
aws_secret_access_key=os.getenv('AWS_SECRET')
bucket_name = os.getenv('DEST_AWS_BUCKET_NAME')

def upload_s3(local_file, s3_file, airline):
    s3 = boto3.client('s3', aws_access_key_id=aws_access_key_id,
                      aws_secret_access_key=aws_secret_access_key)

    try:
        today = datetime.now()
        #date_str = today.strftime('%Y-%m-%d')

        key = f"v0/WebScraping/{airline}/{s3_file}"
        tags = {"s3_url": f"https://{bucket_name}.s3.amazonaws.com/{key}",
                "airline_name": airline,
                "invoice_id": s3_file,
                "created_at": str(today)
                }
        s3.upload_file(local_file,
                       bucket_name,
                       Key=key,
                       ExtraArgs={"Tagging": parse.urlencode(tags)}
                       )
        logger.info("File Uploaded to s3")

        return True, tags['s3_url']
    except FileNotFoundError:
        return False, []
    except NoCredentialsError:
        return False, []
