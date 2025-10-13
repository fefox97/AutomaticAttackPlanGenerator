

from apps.authentication.models import Users
from apps.threat_models import blueprint
from flask import request
from flask import current_app as app
from apps.databases.models import App, AssetTypes, AttackView, MacmUser, Macm, MethodologyView, PentestPhases, ThreatModel
from sqlalchemy import func
from apps.my_modules import converter
from werkzeug.exceptions import NotFound
from apps import render_template

from flask_security import auth_required, current_user

from apps.my_modules.utils import MacmUtils

@blueprint.route('/', methods=['GET'])
@auth_required()
def threat_models():
    try:
        users = Users.query.with_entities(Users.id, Users.username).where(Users.id != current_user.id).all()
        users_dict = converter.tuple_list_to_dict(users)
        usersPerApp = MacmUser.usersPerApp()
        owners = MacmUser.ownerPerApp()
        threat_models = MacmUser.query.join(App).filter(MacmUser.UserID==current_user.id).with_entities(App.AppID, App.Name.label('AppName'), App.Created_at.label('CreatedAt'), MacmUser.IsOwner).all()
        if len(threat_models) == 0:
            threat_models = None
    except Exception as error:
        threat_models = None
        raise error
    return render_template(f"threat_models/threat-models.html", segment=get_segment(request), threat_models=threat_models, users=users, usersPerApp=usersPerApp, owners=owners, users_dict=users_dict)

@blueprint.route('/macm', methods=['GET','POST'])
@auth_required()
def macm():
    try:
        selected_macm = request.args.get('app_id')
        if selected_macm is None or MacmUser.query.filter_by(AppID=selected_macm).count() == 0:
            raise NotFound('MACM not found')
        app_info = App.query.filter_by(AppID=selected_macm).first()
        extra_components = MacmUtils().add_extra_components(selected_macm)
        table = Macm.query.filter_by(App_ID=selected_macm).all()
        if len(table) == 0:
            table = None
        threat_for_each_component = ThreatModel.query.filter_by(AppID=selected_macm).with_entities(ThreatModel.Component_ID, func.count(ThreatModel.Component_ID)).group_by(ThreatModel.Component_ID).all()
        threat_for_each_component = converter.tuple_list_to_dict(threat_for_each_component)
        threat_number = ThreatModel.query.filter_by(AppID=selected_macm).count()
        neo4j_params = {
            "uri": app.config['URI_NEO4J_WSS'],
            "user": app.config['RO_USER_NEO4J'],
            "password": app.config['RO_PASS_NEO4J'],
            "encrypted": app.config['TLS_NEO4J']
        }
        asset_types_colors = AssetTypes.get_colors()
    except NotFound as error:
        raise error
    except Exception as error:
        app.logger.error('Exception occurred while trying to serve ' + request.path, exc_info=True)
        raise Exception('Exception occurred while trying to serve ' + request.path)
    return render_template(f"threat_models/macm.html", segment=get_segment(request), table=table, threat_for_each_component=threat_for_each_component, threat_number=threat_number, selected_macm=selected_macm, extra_components=extra_components, neo4j_params=neo4j_params, app_info=app_info, asset_types_colors=asset_types_colors)

@blueprint.route('/macm-detail', methods=['GET'])
@auth_required()
def macm_detail():
    selected_macm = request.args.get('app_id')
    selected_id = request.args.get('id')
    app_name = App.query.filter_by(AppID=selected_macm).first().Name
    macm_data = Macm.query.filter_by(Component_ID=selected_id, App_ID=selected_macm).first()
    threat_data = ThreatModel.query.filter_by(Component_ID=selected_id, AppID=selected_macm).all()
    return render_template(f"threat_models/macm-detail.html", segment=get_segment(request), macm_data=macm_data, threat_data=threat_data, app_name=app_name)

def get_segment(request):
    try:
        segment = request.path.split('/')
        if segment == '':
            segment = 'index'
        return segment
    except:
        return None
