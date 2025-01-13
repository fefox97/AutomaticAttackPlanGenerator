# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""
from datetime import datetime

from apps.authentication.models import Users
from apps.home import blueprint
from flask import redirect, render_template, request, url_for, jsonify
from flask_login import login_required, current_user
from flask import current_app as app
from apps.databases.models import App, AttackView, Capec, MacmUser, MethodologyCatalogue, MethodologyView, ThreatCatalogue, \
    Macm, ThreatModel, ToolCatalogue, PentestPhases
from sqlalchemy import func
from apps.my_modules import converter
import os
import time
from werkzeug.exceptions import NotFound

from apps.my_modules.utils import MacmUtils

@blueprint.route('/index')
@login_required
def index():
    return redirect(url_for('home_blueprint.penetration_tests'))

@blueprint.route('/capec', methods=['GET'])
@login_required
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
        table = None
        meta_attack_pattern_number = None
        standard_attack_pattern_number = None
        detailed_attack_pattern_number = None
    return render_template(f"home/capec.html", segment=get_segment(request), table=table, meta_attack_pattern_number=meta_attack_pattern_number, standard_attack_pattern_number=standard_attack_pattern_number, detailed_attack_pattern_number=detailed_attack_pattern_number)

@blueprint.route('/capec-detail', methods=['GET'])
@login_required
def capec_detail():
    selected_id = request.args.get('id')
    selected_attack_pattern = Capec.query.filter_by(Capec_ID=selected_id).first()
    return render_template(f"home/capec-detail.html", segment=get_segment(request), data=selected_attack_pattern)

@blueprint.route('/threat-catalog', methods=['GET'])
@login_required
def threat_catalog():
    try:
        table = ThreatCatalogue.query.all()
        if len(table) == 0:
            table = None
    except:
        table = None
    return render_template(f"home/threat-catalog.html", segment=get_segment(request), table=table)

@blueprint.route('/tools', methods=['GET'])
@login_required
def tools():
    try:
        table = ToolCatalogue.query.all()
        if len(table) == 0:
            table = None
    except:
        table = None
    return render_template(f"home/tools.html", segment=get_segment(request), table=table)

@blueprint.route('/methodologies', methods=['GET'])
@login_required
def methodologies():
    try:
        table = MethodologyCatalogue.query.all()
        if len(table) == 0:
            table = None
    except:
        table = None
    return render_template(f"home/methodologies.html", segment=get_segment(request), table=table)

@blueprint.route('/penetration-tests', methods=['GET'])
@login_required
def penetration_tests():
    try:
        users = Users.query.with_entities(Users.id, Users.username).where(Users.id != current_user.id).all()
        users_dict = converter.tuple_list_to_dict(users)
        usersPerApp = MacmUser.usersPerApp()
        owners = MacmUser.ownerPerApp()
        # pentests = MacmUser.query.filter_by(UserID=current_user.id).all()
        pentests = MacmUser.query.join(App).filter(MacmUser.UserID==current_user.id).with_entities(App.AppID, App.Name.label('AppName'), MacmUser.IsOwner).all()
        if len(pentests) == 0:
            pentests = None
    except Exception as error:
        pentests = None
        raise error
    return render_template(f"home/penetration-tests.html", segment=get_segment(request), pentests=pentests, users=users, usersPerApp=usersPerApp, owners=owners, users_dict=users_dict)

@blueprint.route('/macm', methods=['GET','POST'])
@login_required
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
        app.logger.info(neo4j_params)
    except NotFound as error:
        raise error
    except Exception as error:
        app.logger.error('Exception occurred while trying to serve ' + request.path, exc_info=True)
        raise Exception('Exception occurred while trying to serve ' + request.path)
    return render_template(f"home/macm.html", segment=get_segment(request), table=table, attack_for_each_component=attack_for_each_component, attack_number=attack_number, threat_for_each_component=threat_for_each_component, threat_number=threat_number, reports=reports, selected_macm=selected_macm, extra_components=extra_components, neo4j_params=neo4j_params, app_info=app_info)

@blueprint.route('/macm-detail', methods=['GET'])
@login_required
def macm_detail():
    selected_macm = request.args.get('app_id')
    selected_id = request.args.get('id')
    macm_data = Macm.query.filter_by(Component_ID=selected_id, App_ID=selected_macm).first()
    threat_data = ThreatModel.query.filter_by(Component_ID=selected_id, AppID=selected_macm).all()
    methodologies_data = MethodologyView.query.filter_by(Component_ID=selected_id, AppID=selected_macm).all()
    attack_data = AttackView.query.filter_by(Component_ID=selected_id, AppID=selected_macm).all()
    pentest_phases = PentestPhases.query.all()
    av_pentest_phases = AttackView.query.filter_by(Component_ID=selected_id, AppID=selected_macm).with_entities(AttackView.PhaseID, AttackView.PhaseName).distinct().order_by(AttackView.PhaseID).all()
    return render_template(f"home/macm-detail.html", segment=get_segment(request), macm_data=macm_data, attack_data=attack_data, pentest_phases=pentest_phases, av_pentest_phases=av_pentest_phases, threat_data=threat_data, methodologies_data=methodologies_data)

@blueprint.route('/settings', methods=['GET'])
@login_required
def settings():
    excel_file = app.config['THREAT_CATALOG_FILE_NAME']
    path = app.config['DBS_PATH']
    if not os.path.exists(f'{path}/{excel_file}'):
        excel_file = None
    try:
        last_modified = time.ctime(os.path.getmtime(f'{path}/{excel_file}'))
    except:
        last_modified = None
    return render_template(f"admin/settings.html", segment=get_segment(request), excel_file=excel_file, last_modified=last_modified)

@blueprint.route('/support', methods=['GET'])
@login_required
def support():
    return render_template(f"home/support.html", segment=get_segment(request))

# Helper - Extract current page name from request
def get_segment(request):
    try:
        segment = request.path.split('/')[-1]
        if segment == '':
            segment = 'index'
        return segment
    except:
        return None



