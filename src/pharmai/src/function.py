import logging
import os
import json
import os
import json
import smtplib
from email.message import EmailMessage
from datetime import datetime
from typing import Any
import feedparser
from bs4 import BeautifulSoup
from openai import OpenAI
import boto3

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(name)s:%(levelname)s:%(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

# --------------------
# Configuration
# --------------------
RSS_FEEDS = [
    "https://www.fiercepharma.com/rss/xml",
    "https://www.statnews.com/feed/",
    "https://endpts.com/feed/",
]

MAX_ARTICLES = 8

# Get AWS SDK clients
s3_client = boto3.client("s3")
ses_client = boto3.client("ses")
ssm_client = boto3.client("ssm")

S3_BUCKET_NAME = os.environ["S3_BUCKET_NAME"]
SES_FROM_EMAIL_ADDRESS = os.environ["SES_FROM_EMAIL_ADDRESS"]
TO_EMAIL_ADDRESSES_PARAM_NAME = os.environ["TO_EMAIL_ADDRESSES_PARAM_NAME"]
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def handler(event, context):
    """
    Main function to orchestrate the weekly pharma intelligence report generation.
    """
    logger.info(f"event={event}")

    # Fetch and clean articles
    top_articles = fetch_and_clean_articles(RSS_FEEDS, MAX_ARTICLES)

    # Build prompt and get AI analysis
    prompt = build_analysis_prompt(top_articles)
    articles_json = get_ai_analysis(prompt, OPENAI_API_KEY)

    # Build and save HTML report
    html_content = build_html_report(articles_json)
    # TODO copy to S3 behind CDN
    # filename = save_html_report(html_content)

    # Email the report
    send_emails(html_content)

    return "Success"


def fetch_and_clean_articles(feed_urls, max_articles):
    """
    Fetch articles from RSS feeds and clean their summaries.

    Args:
        feed_urls: List of RSS feed URLs
        max_articles: Maximum number of articles to return

    Returns:
        List of dictionaries containing title, link, and summary
    """
    articles = []
    for feed_url in feed_urls:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            raw_summary = entry.get("summary", "")
            clean_summary = BeautifulSoup(raw_summary, "html.parser").get_text(
                separator=" ", strip=True
            )
            articles.append(
                {"title": entry.title, "link": entry.link, "summary": clean_summary}
            )

    # Deduplicate by title
    seen = set()
    unique_articles = []
    for a in articles:
        if a["title"] not in seen:
            seen.add(a["title"])
            unique_articles.append(a)

    logger.info(f"Fetched {len(unique_articles)} articles")

    return unique_articles[:max_articles]


def build_analysis_prompt(articles):
    """
    Build the prompt for OpenAI API based on articles.

    Args:
        articles: List of article dictionaries

    Returns:
        Formatted prompt string
    """
    article_text = ""
    for a in articles:
        article_text += f"- {a['title']} ({a['link']})\n- Summary: {a['summary']}\n\n"

    prompt = f"""
You are a senior pharma and biotech strategy analyst.

Using the articles below, produce a WEEKLY EXECUTIVE INTELLIGENCE BRIEF.

For each article, generate three things:
1. What happened (2-3 concise bullets)
2. SO WHAT: commercial, market access, competitive, or strategic implications
3. Recommended next steps for a competitor in response to this news

Output your results as a JSON array where each item has the keys:
- "title"
- "what_happened"
- "so_what"
- "next_steps"

Articles:
{article_text}
"""
    return prompt


def get_ai_analysis(prompt, api_key):
    """
    Call OpenAI API to analyze articles.

    Args:
        prompt: The analysis prompt
        api_key: OpenAI API key

    Returns:
        Parsed JSON array of article analyses
    """
    logger.info(f"Using AI to generate analysis")
    client = OpenAI(api_key=api_key)

    response = client.responses.create(model="gpt-5-mini", input=prompt)

    output_text = response.output_text

    # Parse JSON output
    try:
        articles_json = json.loads(output_text)
    except:
        # Fallback if GPT output is not valid JSON
        articles_json = [
            {
                "title": "Weekly Brief",
                "what_happened": output_text,
                "so_what": "",
                "next_steps": "",
            }
        ]

    logger.info("Fetched AI analysis of articles")

    return articles_json


def build_html_report(articles_json):
    """
    Build HTML report from analyzed articles.

    Args:
        articles_json: List of analyzed article dictionaries

    Returns:
        HTML content string
    """
    html_content = "<html><body style='font-family: Arial, sans-serif;'>"
    html_content += f"<h2>Weekly Pharma Intelligence Report - {datetime.today().strftime('%Y-%m-%d')}</h2>"

    for article in articles_json:
        title = article.get("title", "No title")
        what = article.get("what_happened", "")
        so_what = article.get("so_what", "")
        next_steps = article.get("next_steps", "")

        html_content += f"<div style='margin-bottom: 20px; border: 1px solid #ccc; padding: 10px; border-radius: 8px;'>"
        html_content += f"<strong style='font-size: 16px;'>{title}</strong><br>"
        html_content += f"<p><strong>What happened:</strong> {what}</p>"
        html_content += f"<p><strong>SO WHAT:</strong> {so_what}</p>"
        html_content += f"<p><strong>Recommended next steps for a competitor:</strong> {next_steps}</p>"
        html_content += "</div>"

    html_content += "</body></html>"
    return html_content


def save_html_report(html_content):
    """
    Save HTML report to file.

    Args:
        html_content: HTML string to save

    Returns:
        Filename of saved report
    """
    today = datetime.today().strftime("%Y-%m-%d")
    filename = f"weekly_pharma_intel_{today}.html"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_content)

    logger.info(f"Saved HTML report: {filename}")
    return filename


def email_report(html_content, sender_email, receiver_email, password):
    """
    Email the HTML report.

    Args:
        html_content: HTML string to email
        sender_email: Sender email address
        receiver_email: Receiver email address
        password: Email account password (App Password for Gmail with 2FA)
    """
    today = datetime.today().strftime("%Y-%m-%d")

    msg = EmailMessage()
    msg["Subject"] = f"Weekly Pharma Intelligence Report - {today}"
    msg["From"] = sender_email
    msg["To"] = receiver_email

    # Plain text fallback
    msg.set_content(
        "Weekly Pharma Intelligence Report attached. Open in HTML-capable email client to see full formatting."
    )
    # HTML version
    msg.add_alternative(html_content, subtype="html")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(sender_email, password)
        smtp.send_message(msg)

    print(f"Email sent with report for {today}")


def send_emails(html_content: str):
    to_email_addresses = get_to_email_addresses()

    for email_address in to_email_addresses:
        send_email_to_recipient(html_content, email_address)


def send_email_to_recipient(html_content: str, to_email_address):
    today = datetime.today().strftime("%Y-%m-%d")
    ses_client.send_email(
        Destination={
            "ToAddresses": [to_email_address],
        },
        Message={
            "Body": {
                "Html": {
                    "Charset": "UTF-8",
                    "Data": html_content,
                },
                "Text": {
                    "Charset": "UTF-8",
                    "Data": "Weekly Pharma Intelligence Report attached. Open in HTML-capable email client to see full formatting.",
                },
            },
            "Subject": {
                "Charset": "UTF-8",
                "Data": f"Weekly Pharma Intelligence Report - {today}",
            },
        },
        Source=SES_FROM_EMAIL_ADDRESS,
    )


def get_to_email_addresses():
    """Get email address recipients"""
    logger.info(f"Fetching ssm param={TO_EMAIL_ADDRESSES_PARAM_NAME}")
    response = ssm_client.get_parameter(
        Name=TO_EMAIL_ADDRESSES_PARAM_NAME, WithDecryption=True
    )
    to_email_addresses_json = response["Parameter"]["Value"]
    to_email_addresses = json.loads(to_email_addresses_json)
    logger.info(f"to_email_addresses={to_email_addresses}")
    return to_email_addresses
