

from flask import flash, redirect, request, url_for
from flask_security import auth_required, current_user, verify_password
from apps.authentication.models import ApiToken
from apps.profile import blueprint
from apps.profile.forms import DeleteAccountForm
from apps import db, render_template
from flask import current_app as app

from apps.authentication.util import send_account_deleted_email
from apps.databases.models import App, MacmUser

@blueprint.route('/profile', methods=['GET'])
@auth_required()
def profile():
    return render_template(f"profile/profile.html", segment=get_segment(request))

@blueprint.route('/delete_account', methods=['GET', 'POST'])
@auth_required()
def delete_account():
    delete_account_form = DeleteAccountForm()
    if delete_account_form.validate_on_submit():
        # Check if the password is correct
        if verify_password(delete_account_form.password.data, current_user.password):
            macm_apps = MacmUser.query.filter_by(UserID=current_user.id, IsOwner=1).all()
            for macm_app in macm_apps:
                App.query.filter_by(AppID=macm_app.AppID).delete()
            db.session.delete(current_user)
            app.user_datastore.delete_user(current_user)
            app.user_datastore.commit()
            send_account_deleted_email(current_user)
            return redirect(url_for('security.logout'))
        else:
            flash('Password is incorrect', 'danger')
            return redirect(url_for('profile_blueprint.delete_account'))

    return render_template(f"security/delete_account.html", segment=get_segment(request), delete_account_form=delete_account_form)

# Helper - Extract current page name from request
def get_segment(request):
    try:
        segment = request.path.split('/')
        if segment == '':
            segment = 'index'
        return segment
    except:
        return None