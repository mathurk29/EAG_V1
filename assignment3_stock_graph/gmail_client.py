import os.path
import base64
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

# Scopes for Gmail
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def get_gmail_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('client_secrets.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('gmail', 'v1', credentials=creds)
    return service

def send_email(sender, to, subject, body_text):
    sender = os.getenv('GMAIL_USER')
    service = get_gmail_service()
    message = MIMEText(body_text)
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    message_body = {'raw': raw}
    send_message = service.users().messages().send(userId="me", body=message_body).execute()
    print(f'Email sent! Message Id: {send_message["id"]}')

# Usage
# service = get_gmail_service()
# send_email(service, "coderswithpitchers@gmail.com", "mathurk29@gmail.com", "Test via Gmail API", "Hello from Python!")
