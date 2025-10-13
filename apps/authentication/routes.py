

from flask import redirect, request, session, url_for
from flask_security import current_user

from flask_dance.contrib.github import github

from apps.authentication import blueprint
from apps.authentication.forms import GithubForm
from apps.authentication.models import Users
from apps import db, render_template
from flask import current_app as app

@blueprint.route("/github")
def login_github():
    """ Github login """
    next_url = request.args.get("next")
    if next_url:
        app.logger.info(f'Next URL: {next_url}')
        session['next_url'] = next_url
    if not github.authorized:
        return redirect(url_for("github.login"))
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
