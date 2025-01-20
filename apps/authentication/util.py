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

def send_account_deleted_email(user):
    """
    Send account delete email to the user
    """
    mail.send_mail(
        from_email=app.config["MAIL_DEFAULT_SENDER"],
        subject="Account Deleted",
        recipient_list=[user.email],
        message=render_template('security/email/account_deleted.html', user=user),
        html_message=render_template('security/email/account_deleted.html', user=user)
    )

def notify_admins(user):
    """
    Notify admins about new user registration
    """
    mail.send_mail(
        from_email=app.config["MAIL_DEFAULT_SENDER"],
        subject="New User Registration",
        recipient_list=[app.config["MAIL_DEFAULT_SENDER"]],
        message=render_template('security/email/new_user.html', user=user),
        html_message=render_template('security/email/new_user.html', user=user)
    )