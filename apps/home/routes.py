# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from apps.authentication.models import Users
from apps.home import blueprint
from flask import redirect, render_template, request, url_for
from flask import current_app as app
from apps.databases.models import App, AttackView, MacmUser, MethodologyView, Settings, Macm, ThreatModel, PentestPhases
from sqlalchemy import func
from apps.my_modules import converter
import os
import time
from werkzeug.exceptions import NotFound

from flask_security import auth_required, current_user, roles_required

from apps.my_modules.utils import MacmUtils

@blueprint.route('/index')
@auth_required()
def index():
    return redirect(url_for('penetration_tests_blueprint.penetration_tests'))

@blueprint.route('/settings', methods=['GET'])
@auth_required()
@roles_required('editor')
def settings():
    excel_file = app.config['THREAT_CATALOG_FILE_NAME']
    path = app.config['DBS_PATH']
    settings = Settings.to_dict()
    if not os.path.exists(f'{path}/{excel_file}'):
        excel_file = None
    try:
        last_modified = time.ctime(os.path.getmtime(f'{path}/{excel_file}'))
    except:
        last_modified = None
    return render_template(f"admin/settings.html", segment=get_segment(request), excel_file=excel_file, last_modified=last_modified, settings=settings)

# Helper - Extract current page name from request
def get_segment(request):
    try:
        segment = request.path.split('/')[-1]
        if segment == '':
            segment = 'index'
        return segment
    except:
        return None



