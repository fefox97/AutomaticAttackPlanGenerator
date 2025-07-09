

from apps.catalogs import blueprint
from flask import request
from flask import current_app as app
from apps.databases.models import AssetTypes, Capec, MethodologyCatalogue, Protocols, ThreatCatalogue, \
    ToolCatalogue

from flask_security import auth_required

from apps import render_template

@blueprint.route('/capec', methods=['GET'])
def capec():
    try:
        table = Capec.query.order_by(Capec.abstraction_order, Capec.Capec_ID).all()
        meta_attack_pattern_number = Capec.query.filter(Capec.Abstraction=='Meta').count()
        standard_attack_pattern_number = Capec.query.filter(Capec.Abstraction=='Standard').count()
        detailed_attack_pattern_number = Capec.query.filter(Capec.Abstraction=='Detailed').count()
        if len(table) == 0:
            table = None
            meta_attack_pattern_number = None
            standard_attack_pattern_number = None
            detailed_attack_pattern_number = None
    except:
        app.logger.error('Exception occurred while trying to serve ' + request.path, exc_info=True)
        table = None
        meta_attack_pattern_number = None
        standard_attack_pattern_number = None
        detailed_attack_pattern_number = None
    return render_template(f"catalogs/capec.html", segment=get_segment(request), table=table, meta_attack_pattern_number=meta_attack_pattern_number, standard_attack_pattern_number=standard_attack_pattern_number, detailed_attack_pattern_number=detailed_attack_pattern_number)

@blueprint.route('/capec-detail', methods=['GET'])
def capec_detail():
    selected_id = request.args.get('id')
    selected_attack_pattern = Capec.query.filter_by(Capec_ID=selected_id).first()
    return render_template(f"catalogs/capec-detail.html", segment=get_segment(request), data=selected_attack_pattern)

@blueprint.route('/threat-catalog', methods=['GET'])
def threat_catalog():
    try:
        table = ThreatCatalogue.query.all()
        if len(table) == 0:
            table = None
    except:
        table = None
    return render_template(f"catalogs/threat-catalog.html", segment=get_segment(request), table=table)

@blueprint.route('/tools', methods=['GET'])
def tools():
    try:
        table = ToolCatalogue.query.all()
        if len(table) == 0:
            table = None
    except:
        table = None
    return render_template(f"catalogs/tools.html", segment=get_segment(request), table=table)

@blueprint.route('/asset-types', methods=['GET'])
def asset_types():
    try:
        table = AssetTypes.query.all()
        if len(table) == 0:
            table = None
    except:
        table = None
    return render_template(f"catalogs/asset-types.html", segment=get_segment(request), table=table)

@blueprint.route('/protocols', methods=['GET'])
def protocols():
    try:
        table = Protocols.query.all()
        if len(table) == 0:
            table = None
    except:
        table = None
    return render_template(f"catalogs/protocols.html", segment=get_segment(request), table=table)

@blueprint.route('/methodologies', methods=['GET'])
def methodologies():
    try:
        table = MethodologyCatalogue.query.all()
        if len(table) == 0:
            table = None
    except:
        table = None
    return render_template(f"catalogs/methodologies.html", segment=get_segment(request), table=table)

# Helper - Extract current page name from request
def get_segment(request):
    try:
        segment = request.path.split('/')
        if segment == '':
            segment = 'index'
        return segment
    except:
        return None



