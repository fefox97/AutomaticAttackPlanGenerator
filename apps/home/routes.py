

from apps.home import blueprint
from flask import redirect, render_template, request, url_for
from flask import current_app as app
from apps.databases.models import Bibliography, Settings
import os
import time

from flask_security import auth_required, roles_required

@blueprint.route('/index')
@auth_required()
def index():
    return redirect(url_for('penetration_tests_blueprint.penetration_tests'))

@blueprint.route('/settings', methods=['GET'])
@auth_required()
@roles_required('editor')
def settings():
    excel_file = Settings.query.filter_by(key='catalogs_filename').first().value if Settings.query.filter_by(key='catalogs_filename').first() else None
    path = app.config['DBS_PATH']
    settings = Settings.to_dict()
    if not os.path.exists(f'{path}/{excel_file}'):
        excel_file = None
    try:
        last_modified = time.ctime(os.path.getmtime(f'{path}/{excel_file}'))
    except:
        last_modified = None
    return render_template(f"admin/settings.html", segment=get_segment(request), excel_file=excel_file, last_modified=last_modified, settings=settings)

@blueprint.route('/about_us', methods=['GET'])
@auth_required()
def about_us():
    references = Bibliography.query.all()
    return render_template('home/about-us.html', segment=get_segment(request), references=references)
    

# Helper - Extract current page name from request
def get_segment(request):
    try:
        segment = request.path.split('/')[-1]
        if segment == '':
            segment = 'index'
        return segment
    except:
        return None



