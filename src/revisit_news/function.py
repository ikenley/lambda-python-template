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
    event_detail = event["detail"]
    s3_bucket = event_detail["s3_bucket"]
    s3_key = event_detail["s3_key"]

    top_recent_articles = get_articles_from_s3(s3_bucket, s3_key)
    historical_articles_result = get_historical_articles()
    send_emails(top_recent_articles, historical_articles_result)
    return "Success"


def get_articles_from_s3(s3_bucket, s3_key):
    """Fetches articles JSON file from a given S3 object"""
    file = get_file_from_s3(s3_bucket, s3_key)
    recent_articles = json.loads(file)
    top_recent_articles = recent_articles[:5]
    return top_recent_articles


def get_file_from_s3(s3_bucket, s3_key):
    response = s3_client.get_object(Bucket=s3_bucket, Key=s3_key)
    object_content = response["Body"].read().decode("utf-8")
    return object_content


def get_historical_articles():
    """Fetches historical articles from random day in history"""
    s3_key = get_random_historical_file()
    date_label = get_date_from_s3_key(s3_key)
    articles = get_articles_from_s3(S3_BUCKET_NAME, s3_key)
    return {"articles": articles, "date_label": date_label}


def get_random_historical_file():
    response = s3_client.list_objects_v2(
        Bucket=S3_BUCKET_NAME,
        Prefix="news/nytimes/mostpopular/emailed/1/2023",
    )
    response_contents = response["Contents"]
    random_element = random.choice(response_contents)
    s3_key = random_element["Key"]
    logger.info(f"get_random_historical_file:s3_key={s3_key}")
    return s3_key


def get_date_from_s3_key(s3_key):
    """Get date from S3 key in format news/nytimes/mostpopular/emailed/1/2023/12/08/2023-12-08-news.json"""
    pattern = r"(\d{4}-\d{2}-\d{2})-news\.json"
    match_object = re.search(pattern, s3_key)
    date_label = match_object.group(1)
    logger.info(f"date_label={date_label}")
    return date_label


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
