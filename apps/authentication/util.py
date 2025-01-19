# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask import render_template, current_app as app

from apps import mail

# Inspiration -> https://www.vitoshacademy.com/hashing-passwords-in-python/

def send_welcome_email(user):
    """
    Send welcome email to the user
    """
    mail.send_mail(
        from_email=app.config["MAIL_DEFAULT_SENDER"],
        subject="Welcome to Pennet",
        recipient_list=[user.email],
        message=render_template('security/email/welcome_github.html', user=user),
        html_message=render_template('security/email/welcome_github.html', user=user)
    )