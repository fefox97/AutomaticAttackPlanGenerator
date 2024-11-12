# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from apps.home import blueprint
from flask import redirect, render_template, request, url_for, make_response
from flask_login import login_required, current_user
from jinja2 import TemplateNotFound
from flask import current_app as app
from apps.databases.models import AttackView, Capec, MacmUser, MethodologyCatalogue, MethodologyView, ThreatCatalogue, Macm, ThreatModel, ToolCatalogue, PentestPhases
from sqlalchemy import func, distinct
from sqlalchemy.dialects import mysql
from apps.my_modules import converter

@blueprint.route('/index')
@login_required
def index():
    return redirect(url_for('home_blueprint.route_template', template='penetration-tests.html'))

@blueprint.route('/<template>', methods=['GET'])
@login_required
def route_template(template):

    try:

        if not template.endswith('.html'):
            template += '.html'

        # Detect the current page
        segment = get_segment(request)
        app.logger.info('Serving ' + template)

        # Serve the file (if exists) from app/templates/home/FILE.html
        if template == 'capec.html':
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
            return render_template(f"home/{template}", segment=segment, table=table, meta_attack_pattern_number=meta_attack_pattern_number, standard_attack_pattern_number=standard_attack_pattern_number, detailed_attack_pattern_number=detailed_attack_pattern_number)

        elif template == 'capec-detail.html':
            selected_id = request.args.get('id')
            selected_attack_pattern = Capec.query.filter_by(Capec_ID=selected_id).first()
            return render_template(f"home/{template}", segment=segment, data=selected_attack_pattern)
        
        elif template == 'threat-catalog.html':
            try:
                table = ThreatCatalogue.query.all()
                if len(table) == 0:
                    table = None
            except:
                table = None
            return render_template(f"home/{template}", segment=segment, table=table)
        
        elif template == 'tools.html':
            try:
                table = ToolCatalogue.query.all()
                if len(table) == 0:
                    table = None
            except:
                table = None
            return render_template(f"home/{template}", segment=segment, table=table)
        
        elif template == 'methodologies.html':
            try:
                table = MethodologyCatalogue.query.all()
                if len(table) == 0:
                    table = None
            except:
                table = None
            return render_template(f"home/{template}", segment=segment, table=table)

        elif template == 'penetration-tests.html':
            try:
                pentests = MacmUser.query.filter_by(UserID=current_user.id).all()
                if len(pentests) == 0:
                    pentests = None
            except:
                pentests = None
            return render_template(f"home/{template}", segment=segment, pentests=pentests)

        elif template == 'macm.html':
            try:
                selected_macm = request.args.get('app_id')
                table = Macm.query.filter_by(App_ID=selected_macm).all()
                if len(table) == 0:
                    table = None
            except:
                table = None
            try:
                attack_for_each_component = AttackView.query.filter_by(AppID=selected_macm).with_entities(AttackView.Component_ID, func.count(AttackView.Component_ID)).group_by(AttackView.Component_ID).all()
                attack_for_each_component = converter.tuple_list_to_dict(attack_for_each_component)
                attack_number = AttackView.query.filter_by(AppID=selected_macm).count()
                threat_for_each_component = ThreatModel.query.filter_by(AppID=selected_macm).with_entities(ThreatModel.Component_ID, func.count(ThreatModel.Component_ID)).group_by(ThreatModel.Component_ID).all()
                threat_for_each_component = converter.tuple_list_to_dict(threat_for_each_component)
                threat_number = ThreatModel.query.filter_by(AppID=selected_macm).count()
            except:
                app.logger.error('Exception occurred while trying to serve ' + request.path, exc_info=True)
                attack_for_each_component = None
                attack_number = None
            return render_template(f"home/{template}", segment=segment, table=table, attack_for_each_component=attack_for_each_component, attack_number=attack_number, threat_for_each_component=threat_for_each_component, threat_number=threat_number)
        
        elif template == 'macm-detail.html':
            selected_macm = request.args.get('app_id')
            selected_id = request.args.get('id')
            macm_data = Macm.query.filter_by(Component_ID=selected_id, App_ID=selected_macm).first()
            threat_data = ThreatModel.query.filter_by(Component_ID=selected_id, AppID=selected_macm).all()
            methodologies_data = MethodologyView.query.filter_by(Component_ID=selected_id, AppID=selected_macm).all()
            attack_data = AttackView.query.filter_by(Component_ID=selected_id, AppID=selected_macm).all()
            pentest_phases = PentestPhases.query.all()
            av_pentest_phases = AttackView.query.filter_by(Component_ID=selected_id, AppID=selected_macm).with_entities(AttackView.PhaseID, AttackView.PhaseName).distinct().order_by(AttackView.PhaseID).all()
            return render_template(f"home/{template}", segment=segment, macm_data=macm_data, attack_data=attack_data, pentest_phases=pentest_phases, av_pentest_phases=av_pentest_phases, threat_data=threat_data, methodologies_data=methodologies_data)

        # Serve the file (if exists) from app/templates/home/FILE.html
        return render_template(f"home/{template}", segment=segment)

    except TemplateNotFound:
        return render_template('errors/page-404.html'), 404

    except:
        app.logger.error('Exception occurred while trying to serve ' + request.path, exc_info=True)
        return render_template('errors/page-404.html'), 500

# Helper - Extract current page name from request
def get_segment(request):
    try:
        segment = request.path.split('/')[-1]
        if segment == '':
            segment = 'index'
        return segment
    except:
        return None
