import email, smtplib, ssl
from typing import List
from MMC import settings
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def load_contacts(file: Path = settings.email_contactList) -> List[str]:
    with open(file) as f:
        lines = f.readlines()
    return [line.strip() for line in lines]
    

def send_email(title,message, contacts:List[str]=[]):
    mail = MIMEMultipart()
    mail["Subject"] = title
    mail.attach(MIMEText(message, "plain"))
    text = mail.as_string()
    with smtplib.SMTP(settings.env.smtp_server, settings.env.smtp_port) as server:
        for receiver in set(load_contacts() + contacts):
            server.sendmail(settings.env.sender_email, receiver, text)

