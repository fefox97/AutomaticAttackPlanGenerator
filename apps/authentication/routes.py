# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

import time
from flask import render_template, redirect, request, url_for
from flask_login import (
    current_user,
    login_user,
    logout_user
)
from flask import current_app as app

from flask_dance.contrib.github import github

from apps import db, login_manager
from apps.authentication import blueprint
from apps.authentication.forms import LoginForm, CreateAccountForm, GithubForm, ResetPasswordForm, ResetPasswordRequestForm
from apps.authentication.models import Users


from apps.authentication.util import send_reset_password_email, verify_pass

@blueprint.route('/')
def route_default():
    return redirect(url_for('authentication_blueprint.login'))

# Login & Registration

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
        user = Users.query.filter_by(username=current_user.username).first()
        user.email = email
        db.session.commit()
        
        return redirect(url_for('home_blueprint.index'))

    return render_template('accounts/add-email.html', form=github_register_form)

@blueprint.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm(request.form)
    if 'login' in request.form:

        # read form data
        username = request.form['username']
        password = request.form['password']

        # Locate user
        user = Users.query.filter_by(username=username).first()

        # Check the password
        if user and verify_pass(password, user.password):

            login_user(user)
            return redirect(url_for('authentication_blueprint.route_default'))

        # Something (user or pass) is not ok
        return render_template('accounts/login.html',
                                msg='Wrong user or password',
                                form=login_form)

    if not current_user.is_authenticated:
        return render_template('accounts/login.html',
                                form=login_form)
    return redirect(url_for('home_blueprint.index'))


@blueprint.route('/register', methods=['GET', 'POST'])
def register():
    create_account_form = CreateAccountForm(request.form)
    if 'register' in request.form:

        username = request.form['username']
        email = request.form['email']

        # Check usename exists
        user = Users.query.filter_by(username=username).first()
        if user:
            return render_template('accounts/register.html',
                                    msg='Username already registered',
                                    success=False,
                                    form=create_account_form)

        # Check email exists
        user = Users.query.filter_by(email=email).first()
        if user:
            return render_template('accounts/register.html',
                                    msg='Email already registered',
                                    success=False,
                                    form=create_account_form)

        # else we can create the user
        user = Users(**request.form)
        db.session.add(user)
        db.session.commit()

        # Delete user from session
        logout_user()
        
        return render_template('accounts/register.html',
                                msg='Account created successfully.',
                                success=True,
                                form=create_account_form)

    else:
        return render_template('accounts/register.html', form=create_account_form)


@blueprint.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('authentication_blueprint.login'))


@blueprint.route('/reset-password-request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('home_blueprint.index'))
    
    reset_password_form = ResetPasswordRequestForm(request.form)
    if 'reset' in request.form:

        email = request.form['email']
        user = Users.query.filter_by(email=email).first()

        if user:
            app.logger.info(time.time())
            app.logger.info(user.updated_on.timestamp())
            time_since_last_reset = time.time() - user.updated_on.timestamp()
            reset_password_limit = int(app.config['RESET_PASSWORD_LIMIT'])
            if time_since_last_reset < reset_password_limit:
                delta_time = int((reset_password_limit - time_since_last_reset) / 60)+1
                return render_template('accounts/reset-password-request.html',
                                        msg=f'Please wait {delta_time} minutes before requesting another password reset',
                                        success=False,
                                        form=reset_password_form)
            # send email
            app.logger.info('Reset password for user %s', user.username)
            send_reset_password_email(user)
        else:
            app.logger.info('Email does not exist %s', email)
        
        return render_template('accounts/reset-password-request.html',
                                msg='Password reset link was sent to your email address if it exists',
                                success=True,
                                form=reset_password_form)

    return render_template('accounts/reset-password-request.html', form=reset_password_form)

@blueprint.route('/reset-password/<token>/<int:user_id>', methods=['GET', 'POST'])
def reset_password(token, user_id):
    if current_user.is_authenticated:
        return redirect(url_for('home_blueprint.index'))

    user = Users.validate_reset_password_token(token, user_id)
    if not user:
        return render_template('accounts/reset-password.html', msg='Invalid or expired token', form=None)
    
    reset_password_form = ResetPasswordForm(request.form)
    if 'reset' in request.form and reset_password_form.validate_on_submit():

        password = request.form['password']
        user.update_password(password)
        db.session.commit()

        return render_template('accounts/reset-password.html', msg='Password updated successfully', form=None)
    
    return render_template('accounts/reset-password.html', form=reset_password_form)

# Errors

@login_manager.unauthorized_handler
def unauthorized_handler():
    return render_template('errors/page-403.html'), 403


@blueprint.errorhandler(403)
def access_forbidden(error):
    return render_template('errors/page-403.html'), 403


@blueprint.errorhandler(404)
def not_found_error(error):
    return render_template('errors/page-404.html'), 404


@blueprint.errorhandler(500)
def internal_error(error):
    return render_template('errors/page-500.html'), 500
