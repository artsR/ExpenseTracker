from flask import render_template, current_app
from eTracker.email import send_email



def send_password_reset_link(user):
    token = user.get_reset_password_token()
    send_email('eTRACKER Password Recovery',
                sender=current_app.config['MAIL_DEFAULT_SENDER'],
                recipients=[user.email],
                body_txt=render_template('auth/reset_password_email.txt',
                                        user=user, token=token),
                body_html=render_template('auth/reset_password_email.html',
                                        user=user, token=token))
