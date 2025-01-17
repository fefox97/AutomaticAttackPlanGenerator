# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask import render_template, redirect, request, url_for
from flask import current_app as app

from flask_security import url_for_security, current_user, user_registered

from flask_dance.contrib.github import github

from apps.authentication import blueprint
from apps.authentication.forms import GithubForm
from apps.authentication.models import Users
from apps import db, security

@blueprint.route('/')
def route_default():
    return redirect(url_for_security('login'))

@blueprint.route("/github")
def login_github():
    """ Github login """
    if not github.authorized:
        return redirect(url_for("github.login"))

    res = github.get("/user")
    return redirect(url_for('home_blueprint.index'))

@blueprint.route("/register-github", methods=['GET', 'POST'])
def register_github():
    github_register_form = GithubForm(request.form)
    if 'add_email' in request.form:

        email = request.form['email']

        if Users.query.filter_by(email=email).first():
            return redirect(url_for('authentication_blueprint.register_github', msg='Email already exists'))

        user = Users.query.filter_by(username=current_user.username).first()
        user.email = email
        db.session.commit()
        
        return redirect(url_for('home_blueprint.index'))

    return render_template('accounts/add-email.html', form=github_register_form)

# Errors

@blueprint.errorhandler(403)
def access_forbidden(error):
    return render_template('errors/page-403.html'), 403


@blueprint.errorhandler(404)
def not_found_error(error):
    return render_template('errors/page-404.html'), 404


@blueprint.errorhandler(500)
def internal_error(error):
    return render_template('errors/page-500.html'), 500
