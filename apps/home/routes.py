

from datetime import time
import os
from apps import render_template
from apps.home import blueprint
from flask import redirect, request, url_for
from flask import current_app as app
from apps.databases.models import AssetTypes, Attack, App, Bibliography, Capec, Macm, MethodologyCatalogue, Protocols, Settings, ThreatCatalogue, ThreatModel, ToolCatalogue
from flask_security import auth_required, roles_required


from sqlalchemy import func

@blueprint.route('/')
@blueprint.route('/index')
def index():
    """
    Redirect to the home page.
    """
    return redirect(url_for('home_blueprint.home'))

@blueprint.route('/home')
def home():
    """
    Redirect to the home page.
    """

    attack_counts = Attack.query.count()
    app_counts = App.query.count()
    asset_counts = Macm.query.count()
    threat_counts = ThreatModel.query.count()
    asset_types_counts = AssetTypes.query.count()
    threat_catalogue_counts = ThreatCatalogue.query.count()
    capec_counts = Capec.query.count()
    methodology_catalogue_counts = MethodologyCatalogue.query.count()
    tool_catalogue_counts = ToolCatalogue.query.count()
    protocol_catalogue_counts = Protocols.query.count()

    return render_template(
        'home/home.html',
        segment=get_segment(request),
        attack_counts=attack_counts,
        app_counts=app_counts,
        asset_counts=asset_counts,
        threat_counts=threat_counts,
        asset_types_counts=asset_types_counts,
        protocol_catalogue_counts=protocol_catalogue_counts,
        threat_catalogue_counts=threat_catalogue_counts,
        capec_counts=capec_counts,
        methodology_catalogue_counts=methodology_catalogue_counts,
        tool_catalogue_counts=tool_catalogue_counts
    )

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



