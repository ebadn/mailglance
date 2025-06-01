from flask import Flask, redirect, request, session, jsonify
from flask_cors import CORS
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import os
import base64
import re
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from openai import AsyncOpenAI
from datetime import datetime, timedelta
import redis
import asyncio
import nest_asyncio

# Load environment variables
load_dotenv()
openai_api_key = os.getenv("OPENAI_SECRET_KEY")
client = AsyncOpenAI(api_key=openai_api_key)

# Redis setup
redis_client = redis.Redis(host='localhost', port=6379, db=0)

semaphore = asyncio.Semaphore(20)

app = Flask(__name__)
CORS(app, supports_credentials=True, origins=["http://localhost:3000"])
app.secret_key = os.getenv("FLASK_SECRET_KEY")
app.config["SESSION_COOKIE_SAMESITE"] = "None"
app.config["SESSION_COOKIE_SECURE"] = False

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

GOOGLE_CLIENT_SECRETS_FILE = "credentials.json"
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
REDIRECT_URI = "http://localhost:5000/oauth2callback"


@app.route("/")
def home():
    return jsonify({"message": "MailGlance Backend Running. Visit /authorize to log in."})


@app.route("/authorize")
def authorize():
    flow = Flow.from_client_secrets_file(
        GOOGLE_CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )
    auth_url, state = flow.authorization_url(prompt='consent')
    session["state"] = state
    return redirect(auth_url)


@app.route("/oauth2callback")
def oauth2callback():
    flow = Flow.from_client_secrets_file(
        GOOGLE_CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )
    flow.fetch_token(authorization_response=request.url)
    credentials = flow.credentials

    with open('token.json', 'w') as token_file:
        token_file.write(credentials.to_json())

    return redirect("http://localhost:3000/emails")


@app.route('/emails')
async def get_emails():
    days = int(request.args.get('days', 7))
    detail = request.args.get('detail', 'short')

    try:
        emails = await list_emails(days=days, detail=detail)
        return jsonify(emails)
    except Exception as e:
        print(f"Error in /emails route: {e}")
        return jsonify({"error": "Could not fetch emails"}), 500


def clean_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    for tag in soup(['style', 'script', 'footer', 'head', 'meta', 'link']):
        tag.decompose()
    footer_keywords = ['unsubscribe', 'copyright',
                       'powered by', 'you are receiving this']
    text_blocks = soup.get_text(separator='\n').splitlines()
    cleaned_lines = [line.strip() for line in text_blocks if line.strip()
                     and not any(kw in line.lower() for kw in footer_keywords)]
    return ' '.join(cleaned_lines)


async def list_emails(days=7, detail='short'):
    creds = Credentials.from_authorized_user_file('token.json')
    service = build('gmail', 'v1', credentials=creds)

    time_from = (datetime.utcnow() - timedelta(days=days)).isoformat() + 'Z'
    query = f"is:unread after:{time_from.split('T')[0]}"

    results = service.users().messages().list(
        userId='me', q=query, labelIds=['INBOX']
    ).execute()

    messages = results.get('messages', [])[:20]

    tasks = [process_message(service, message['id'], detail)
             for message in messages]
    return await asyncio.gather(*tasks)


async def process_message(service, msg_id, detail):
    msg = service.users().messages().get(
        userId='me', id=msg_id, format='full'
    ).execute()
    payload = msg.get('payload')
    headers = payload.get('headers')

    subject = next((h['value']
                   for h in headers if h['name'] == 'Subject'), "No Subject")
    from_email = next((h['value']
                      for h in headers if h['name'] == 'From'), "Unknown")

    body = ''
    parts = payload.get('parts')
    if parts:
        for part in parts:
            mime_type = part.get('mimeType')
            data = part.get('body', {}).get('data')
            if mime_type == 'text/plain' and data:
                body = base64.urlsafe_b64decode(
                    data.encode('UTF-8')).decode('utf-8')
                break
            elif mime_type == 'text/html' and data:
                html = base64.urlsafe_b64decode(
                    data.encode('UTF-8')).decode('utf-8')
                body = clean_html(html)
                break
    else:
        data = payload.get('body', {}).get('data')
        if data:
            body = base64.urlsafe_b64decode(
                data.encode('UTF-8')).decode('utf-8')

    soup = BeautifulSoup(body, 'html.parser')
    cleaned_text = soup.get_text(separator='\n', strip=True)

    cache_key = generate_cache_key(msg_id, detail)
    cached_summary = redis_client.get(cache_key)

    if cached_summary:
        summary = cached_summary.decode('utf-8')
    else:
        summary = await async_summarize_email(cleaned_text, detail)
        redis_client.setex(cache_key, timedelta(minutes=30), summary)

    return {
        'id': msg_id,
        'subject': subject,
        'from': from_email,
        'body': cleaned_text,
        'summary': summary,
    }


def generate_cache_key(email_id, detail):
    return f"summary:{email_id}:{detail}"


def clean_email_body(body):
    body = re.sub(r'\s+', ' ', body)
    body = re.sub(r'[^\x20-\x7E]+', ' ', body)
    return body.strip()


async def async_summarize_email(body, detail='short'):
    if len(body) < 50:
        return "Email too short to summarize."

    length_map = {
        'short': (25, 35),
        'medium': (50, 65),
        'long': (100, 130)
    }
    min_words, max_words = length_map.get(detail, (25, 35))

    try:
        cleaned_body = clean_email_body(body)
        prompt = f"Summarize the following email in 25 - 40 words strictly. More than 40 words not allowed:\n\n{cleaned_body}"

        async with semaphore:
            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system",
                        "content": "You are MailGlance, an AI assistant that writes clear summaries of email threads. Extract the main points (who, what, when, action items) . Do not use text formatting as bold fonts or italic fonts (Like **TEXT**). Just plain simple text."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=600
            )

        summary = response.choices[0].message.content.strip()

        if not summary or "i'm sorry" in summary.lower() or "could not summarize" in summary.lower():
            return "Could not summarize this email. :("

        return summary

    except Exception as e:
        print(f"Error while summarizing: {e}")
        return "Could not summarize this email. :("


if __name__ == "__main__":
    nest_asyncio.apply()
    app.run(port=5000, debug=True)
