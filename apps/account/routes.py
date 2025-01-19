

from flask import flash, redirect, render_template, request, url_for
from flask_security import auth_required, current_user, url_for_security, verify_password
from apps.account import blueprint
from apps.account.forms import DeleteAccountForm
from apps import db
from flask import current_app as app

from apps.authentication.util import send_account_deleted_email

@blueprint.route('/profile', methods=['GET'])
@auth_required()
def profile():
    return render_template(f"account/profile.html", segment=get_segment(request))

@blueprint.route('/delete_account', methods=['GET', 'POST'])
@auth_required()
def delete_account():
    delete_account_form = DeleteAccountForm()
    if delete_account_form.validate_on_submit():
        # Check if the password is correct
        if verify_password(delete_account_form.password.data, current_user.password):
            send_account_deleted_email(current_user)
            app.user_datastore.delete_user(current_user)
            app.user_datastore.commit()
            return redirect(url_for('security.logout'))
        else:
            flash('Password is incorrect', 'danger')
            return redirect(url_for('account_blueprint.delete_account'))

    return render_template(f"security/delete_account.html", segment=get_segment(request), delete_account_form=delete_account_form)

# Helper - Extract current page name from request
def get_segment(request):
    try:
        segment = request.path.split('/')[-1]
        if segment == '':
            segment = 'index'
        return segment
    except:
        return None