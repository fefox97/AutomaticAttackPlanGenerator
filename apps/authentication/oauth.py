# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from datetime import datetime
from flask import current_app as app, abort
from flask_security import current_user, login_user
from flask_dance.consumer import oauth_authorized, oauth_error
from flask_dance.contrib.github import github, make_github_blueprint
from flask_dance.consumer.storage.sqla import SQLAlchemyStorage
from sqlalchemy.orm.exc import NoResultFound
from apps.authentication.util import send_welcome_email
from apps.config import Config
from .models import Users, db, OAuth
from flask import redirect, url_for

github_blueprint = make_github_blueprint(
    client_id=Config.GITHUB_CLIENT_ID,
    client_secret=Config.GITHUB_CLIENT_SECRET,
    scope = 'user',
    storage=SQLAlchemyStorage(
        OAuth,
        db.session,
        user=current_user,
        user_required=False,        
    ),
)

@oauth_authorized.connect_via(github_blueprint)
def github_logged_in(blueprint, token):
    info = github.get("/user")
    email_info = github.get("/user/emails")
    account_info = info.json()

    if info.ok:

        username = account_info["login"]
        email = email_info.json()[0]["email"]

        query = Users.query.filter_by(username=username)

        try:
            user = query.one()
            login_user(user)
        except NoResultFound:
            user = app.user_datastore.create_user(
                username=username,
                email=email,
                confirmed_at=datetime.now(),
                password=None
            )
            app.user_datastore.commit()
            login_user(user)

        if email is None:
            return redirect(url_for('authentication_blueprint.register_github'))
        else:
            send_welcome_email(user)

@oauth_error.connect_via(github_blueprint)
def github_error(blueprint, error, error_description=None, error_uri=None):
    return "Error: {0}".format(error_description)