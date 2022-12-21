#!/usr/bin/python


import email,smtplib,ssl
from datetime import date
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def send_capture(file):
    subject = "Capture " + date.today()
    sender_email = "test@test.de"
    receiver_email = "test@test.de"
    password = "test123"

    #Create a multipart message and set headers
    message = MIMEMultipart()
    message["From"] = sender_email
    message["to"] = receiver_email
    message["Subject"] = subject
    message["Bcc"] = receiver_email #1,N receiver

    #open txt file in binary mode
    with open(file,"rb") as attachment:
    #add file as application/ocetet-stream
    #email client can usually download this automatically as attachment
        part = MIMEBase("application","octet-stream")
        part.set_payload(attachment.read())

    #encode file in ASCII characters to send by email
    encoders.encode_base64(part)
    #add header as key/value pair to attachment part
    part.add_header(
    "Content-Disposition",
    f"attachment; filename={file}"
    )

    #add attachment to message and convert message to string
    message.attach(part)
    text = message.as_string()

    #login
    context = ssl.create_default_context()
    try:
        server = smtplib.SMTP("SMTP.office365.com", 587)
        server.ehlo() # Can be omitted
        server.starttls(context=context) #secure connection
        server.ehlo() # Can be omitted
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, text)
    except Exception:
        server.quit()
        return False

    server.quit()
    return True
