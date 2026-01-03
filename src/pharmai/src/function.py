import logging
import os
from datetime import date
import json
import random
import re
from urllib.request import Request, urlopen
import boto3

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(name)s:%(levelname)s:%(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

# Get AWS SDK clients
s3_client = boto3.client("s3")
ses_client = boto3.client("ses")
ssm_client = boto3.client("ssm")

S3_BUCKET_NAME = os.environ["S3_BUCKET_NAME"]
SES_FROM_EMAIL_ADDRESS = os.environ["SES_FROM_EMAIL_ADDRESS"]
TO_EMAIL_ADDRESSES_PARAM_NAME = os.environ["TO_EMAIL_ADDRESSES_PARAM_NAME"]


def handler(event, context):
    logger.info(f"event={event}")
    return "Success"


def send_emails(recent_articles, historical_articles_result):
    to_email_addresses = get_to_email_addresses()

    recent_message = create_article_list_message(recent_articles)
    historical_message = create_article_list_message(
        historical_articles_result["articles"]
    )
    historical_date = historical_articles_result["date_label"]

    for email_address in to_email_addresses:
        send_email_to_recipient(
            recent_message, historical_message, historical_date, email_address
        )


def send_email_to_recipient(
    recent_message, historical_message, historical_date, to_email_address
):
    ses_client.send_email(
        Destination={
            "ToAddresses": [to_email_address],
        },
        Message={
            "Body": {
                "Html": {
                    "Charset": "UTF-8",
                    "Data": f"""The following stories are most emailed NYT artices in the past day:
                    <ol>
                    {recent_message["html_list"]}
                    </ol>
                    The following stories were the most emailed NYT artices on {historical_date}:
                    <ol>
                    {historical_message["html_list"]}
                    </ol>
                    """,
                },
                "Text": {
                    "Charset": "UTF-8",
                    "Data": f"""The following stories are most emailed NYT artices in the past day:
                    {recent_message["text_list"]}
                    The following stories were the most emailed NYT artices on {historical_date}:
                    {historical_message["text_list"]}
                    """,
                },
            },
            "Subject": {
                "Charset": "UTF-8",
                "Data": "Most Emailed NYT Stories",
            },
        },
        Source=SES_FROM_EMAIL_ADDRESS,
    )


def get_to_email_addresses():
    """Get email address recipients"""
    response = ssm_client.get_parameter(
        Name=TO_EMAIL_ADDRESSES_PARAM_NAME, WithDecryption=True
    )
    to_email_addresses_json = response["Parameter"]["Value"]
    to_email_addresses = json.loads(to_email_addresses_json)
    logger.info(f"to_email_addresses={to_email_addresses}")
    return to_email_addresses


def create_article_list_message(articles):
    """Create HTML and plaintext-formatted lists for a given list of articles"""
    html_list = "".join(
        [f"""<li><a href="{a['url']}">{a["title"]}</a></li>""" for a in articles]
    )
    text_list = "".join([f"""- {a["title"]}: {a['url']}\n""" for a in articles])
    return {"html_list": html_list, "text_list": text_list}
