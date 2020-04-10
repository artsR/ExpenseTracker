from threading import Thread
from flask import current_app
from flask_mail import Message
from eTracker import mail



def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


def send_email(subject, sender, recipients, body_txt, body_html):

    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = body_txt
    msg.html = body_html
    mail.send(msg)

    Thread(target=send_async_email,
            args=(current_app._get_current_object(), msg)
    ).start()
