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
from openai import OpenAI

# Load environment variables
load_dotenv()
openai_api_key = os.getenv("OPENAI_SECRET_KEY")
client = OpenAI(api_key=openai_api_key)

app = Flask(__name__)
CORS(app, supports_credentials=True, origins=["http://localhost:3000"])
app.secret_key = os.getenv("FLASK_SECRET_KEY")
app.config["SESSION_COOKIE_SAMESITE"] = "None"
app.config["SESSION_COOKIE_SECURE"] = False
app.secret_key = os.getenv("FLASK_SECRET_KEY")

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

    service = build('gmail', 'v1', credentials=credentials)

    results = service.users().messages().list(
        userId='me', labelIds=['INBOX'], maxResults=3).execute()
    messages = results.get('messages', [])

    for msg in messages:
        msg_data = service.users().messages().get(
            userId='me', id=msg['id']).execute()
        subject = ''
        for header in msg_data['payload']['headers']:
            if header['name'] == 'Subject':
                subject = header['value']
        print("Subject:", subject)

    return redirect("http://localhost:3000/emails")


@app.route('/emails')
def get_emails():
    # if 'state' not in session:
    #     return jsonify({"error": "Not logged in"}), 401
    emails = list_emails()
    return jsonify(emails)


def clean_html(html):
    soup = BeautifulSoup(html, 'html.parser')

    for tag in soup(['style', 'script', 'footer', 'head', 'meta', 'link']):
        tag.decompose()

    footer_keywords = ['unsubscribe', 'copyright',
                       'powered by', 'you are receiving this']
    text_blocks = soup.get_text(separator='\n').splitlines()

    cleaned_lines = []
    for line in text_blocks:
        line = line.strip()
        if line and not any(kw in line.lower() for kw in footer_keywords):
            cleaned_lines.append(line)

    return ' '.join(cleaned_lines)


def list_emails():
    creds = Credentials.from_authorized_user_file('token.json')
    service = build('gmail', 'v1', credentials=creds)

    results = service.users().messages().list(
        userId='me', labelIds=['INBOX'], maxResults=5).execute()
    messages = results.get('messages', [])

    email_data = []

    for message in messages:
        msg = service.users().messages().get(
            userId='me', id=message['id'], format='full').execute()
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
        readable_summary = summarize_email(cleaned_text)

        print("\nRaw Email from:", from_email)
        print("Subject:", subject)
        print("Body:\n", body)
        print("Summary:\n", readable_summary)
        print("-" * 80)

        email_data.append({
            'id': message['id'],
            'subject': subject,
            'from': from_email,
            'body': cleaned_text,
            'summary': readable_summary,
        })

    return email_data


def clean_email_body(body):
    body = re.sub(r'\s+', ' ', body)
    body = re.sub(r'[^\x20-\x7E]+', ' ', body)
    body = body.strip()
    return body


def summarize_email(body):
    if len(body) < 50:
        return "Email too short to summarize."

    try:
        cleaned_body = clean_email_body(body)
        prompt = (
            "Summarize the following email in 2-3 concise sentences, focusing on the important points:\n\n"
            f"{cleaned_body}"
        )

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes email content."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=200
        )

        summary = response.choices[0].message.content.strip()

        if not summary or "I'm sorry" in summary or "could not summarize" in summary.lower():
            return "Could not summarize this email. :("

        return summary

    except Exception as e:
        print(f"Error while summarizing: {e}")
        return "Could not summarize this email. :("


if __name__ == "__main__":
    app.run(port=5000, debug=True)
    # Jeb
