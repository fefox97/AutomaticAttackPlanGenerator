

from apps import render_template
from apps.authentication.models import Users
from apps.databases.models import App, AssetTypes, MacmUser
from apps.macm import blueprint
from flask import request
from flask import current_app as app
from flask_security import auth_required, current_user
from werkzeug.exceptions import NotFound

from apps.macm.forms import UploadMacmForm
from apps.my_modules import converter



@blueprint.route('/', methods=['GET'])
@auth_required()
def macm():
    try:
        upload_macm_form = UploadMacmForm(request.form)
        upload_docker_compose_form = UploadMacmForm(request.form)
        users = Users.query.with_entities(Users.id, Users.username).where(Users.id != current_user.id).all()
        users_dict = converter.tuple_list_to_dict(users)
        usersPerApp = MacmUser.usersPerApp()
        owners = MacmUser.ownerPerApp()
        macms = MacmUser.query.join(App).filter(MacmUser.UserID==current_user.id).with_entities(App.AppID, App.Name.label('AppName'), App.Created_at.label('CreatedAt'), MacmUser.IsOwner).all()
        if len(macms) == 0:
            macms = None
    except Exception as error:
        macms = None
        raise error
    return render_template('macm/macm-manager.html', segment=get_segment(request), macms=macms, users=users, usersPerApp=usersPerApp, owners=owners, users_dict=users_dict, upload_macm_form=upload_macm_form, upload_docker_compose_form=upload_docker_compose_form)

@blueprint.route('/macm-viewer', methods=['GET'])
@auth_required()
def macm_viewer():
    selected_macm = request.args.get('app_id')
    app_info = App.query.filter_by(AppID=selected_macm).first()
    if selected_macm is None or MacmUser.query.filter_by(AppID=selected_macm).count() == 0 or app_info is None:
        raise NotFound('MACM not found')
    neo4j_params = {
            "uri": app.config['URI_NEO4J_WSS'],
            "user": app.config['USER_NEO4J'],
            "password": app.config['PASS_NEO4J'],
            "encrypted": app.config['TLS_NEO4J']
        }
    asset_types_colors = AssetTypes.get_colors()
    return render_template('macm/macm-viewer.html', segment=get_segment(request), selected_macm=selected_macm, neo4j_params=neo4j_params, asset_types_colors=asset_types_colors, app_info=app_info)

# Helper - Extract current page name from request
def get_segment(request):
    try:
        segment = request.path.split('/')[-1]
        if segment == '':
            segment = 'macm'
        return segment
    except:
        return None



