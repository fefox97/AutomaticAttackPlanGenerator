

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
