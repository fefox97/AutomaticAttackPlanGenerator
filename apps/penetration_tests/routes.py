

from apps.penetration_tests.forms import UploadMacmForm
from apps.authentication.models import Users
from apps.penetration_tests import blueprint
from flask import request
from flask import current_app as app
from apps.databases.models import App, AssetTypes, AttackView, MacmUser, MethodologyView, Macm, ThreatModel, PentestPhases
from sqlalchemy import func
from apps.my_modules import converter
from werkzeug.exceptions import NotFound
from apps import render_template

from flask_security import auth_required, current_user

from apps.my_modules.utils import MacmUtils

@blueprint.route('/', methods=['GET'])
@auth_required()
def penetration_tests():
    try:
        upload_macm_form = UploadMacmForm(request.form)
        users = Users.query.with_entities(Users.id, Users.username).where(Users.id != current_user.id).all()
        users_dict = converter.tuple_list_to_dict(users)
        usersPerApp = MacmUser.usersPerApp()
        owners = MacmUser.ownerPerApp()
        pentests = MacmUser.query.join(App).filter(MacmUser.UserID==current_user.id).with_entities(App.AppID, App.Name.label('AppName'), App.Created_at.label('CreatedAt'), MacmUser.IsOwner).all()
        if len(pentests) == 0:
            pentests = None
    except Exception as error:
        pentests = None
        raise error
    return render_template(f"penetration_tests/penetration-tests.html", segment=get_segment(request), pentests=pentests, users=users, usersPerApp=usersPerApp, owners=owners, users_dict=users_dict, upload_macm_form=upload_macm_form)

@blueprint.route('/macm', methods=['GET','POST'])
@auth_required()
def macm():
    try:
        selected_macm = request.args.get('app_id')
        if selected_macm is None or MacmUser.query.filter_by(AppID=selected_macm).count() == 0:
            raise NotFound('MACM not found')
        app_info = App.query.filter_by(AppID=selected_macm).first()
        reports = AttackView.query.filter_by(AppID=selected_macm).with_entities(AttackView.Attack_Number, AttackView.Tool_ID, AttackView.Tool_Name, AttackView.Attack_Pattern, AttackView.Capec_ID, AttackView.Threat_ID, AttackView.Asset_Type, AttackView.Threat, AttackView.Component_ID, AttackView.Asset, AttackView.AppID, AttackView.ReportFiles, AttackView.Report_Parser).where(AttackView.ReportFiles.isnot(None)).distinct().all()
        extra_components = MacmUtils().add_extra_components(selected_macm)
        table = Macm.query.filter_by(App_ID=selected_macm).all()
        if len(table) == 0:
            table = None
        attack_for_each_component = AttackView.query.filter_by(AppID=selected_macm).with_entities(AttackView.Component_ID, func.count(AttackView.Component_ID)).group_by(AttackView.Component_ID).all()
        attack_for_each_component = converter.tuple_list_to_dict(attack_for_each_component)
        attack_number = AttackView.query.filter_by(AppID=selected_macm).count()
        threat_for_each_component = ThreatModel.query.filter_by(AppID=selected_macm).with_entities(ThreatModel.Component_ID, func.count(ThreatModel.Component_ID)).group_by(ThreatModel.Component_ID).all()
        threat_for_each_component = converter.tuple_list_to_dict(threat_for_each_component)
        threat_number = ThreatModel.query.filter_by(AppID=selected_macm).count()
        neo4j_params = {
            "uri": app.config['URI_NEO4J_WSS'],
            "user": app.config['USER_NEO4J'],
            "password": app.config['PASS_NEO4J'],
            "encrypted": app.config['TLS_NEO4J']
        }
        asset_types_colors = AssetTypes.get_colors()
    except NotFound as error:
        raise error
    except Exception as error:
        app.logger.error('Exception occurred while trying to serve ' + request.path, exc_info=True)
        raise Exception('Exception occurred while trying to serve ' + request.path)
    return render_template(f"penetration_tests/macm.html", segment=get_segment(request), table=table, attack_for_each_component=attack_for_each_component, attack_number=attack_number, threat_for_each_component=threat_for_each_component, threat_number=threat_number, reports=reports, selected_macm=selected_macm, extra_components=extra_components, neo4j_params=neo4j_params, app_info=app_info, asset_types_colors=asset_types_colors)

@blueprint.route('/macm-detail', methods=['GET'])
@auth_required()
def macm_detail():
    selected_macm = request.args.get('app_id')
    selected_id = request.args.get('id')
    app_name = App.query.filter_by(AppID=selected_macm).first().Name
    macm_data = Macm.query.filter_by(Component_ID=selected_id, App_ID=selected_macm).first()
    threat_data = ThreatModel.query.filter_by(Component_ID=selected_id, AppID=selected_macm).all()
    methodologies_data = MethodologyView.query.filter_by(Component_ID=selected_id, AppID=selected_macm).all()
    attack_data = AttackView.query.filter_by(Component_ID=selected_id, AppID=selected_macm).all()
    pentest_phases = PentestPhases.query.all()
    av_pentest_phases = AttackView.query.filter_by(Component_ID=selected_id, AppID=selected_macm).with_entities(AttackView.PhaseID, AttackView.PhaseName).distinct().order_by(AttackView.PhaseID).all()
    return render_template(f"penetration_tests/macm-detail.html", segment=get_segment(request), macm_data=macm_data, attack_data=attack_data, pentest_phases=pentest_phases, av_pentest_phases=av_pentest_phases, threat_data=threat_data, methodologies_data=methodologies_data, app_name=app_name)

# Helper - Extract current page name from request
def get_segment(request):
    try:
        segment = request.path.split('/')
        if segment == '':
            segment = 'index'
        return segment
    except:
        return None
