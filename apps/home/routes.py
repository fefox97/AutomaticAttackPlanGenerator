# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from apps.home import blueprint
from flask import redirect, render_template, request, url_for, make_response
from flask_login import login_required, current_user
from jinja2 import TemplateNotFound
from flask import current_app as app
from apps.databases.models import AttackView, Capec, ThreatCatalog, Macm, ToolCatalog
from sqlalchemy import func, distinct
from sqlalchemy.dialects import mysql
from apps.my_modules import converter

# @login_required
@blueprint.route('/index')
def index():
    return redirect(url_for('home_blueprint.route_template', template='macm.html'))

# @login_required
@blueprint.route('/<template>', methods=['GET'])
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
                if len(table) == 0:
                    table = None
            except:
                table = None
            return render_template(f"home/{template}", segment=segment, table=table)

        elif template == 'capec-detail.html':
            selected_id = request.args.get('id')
            selected_attack_pattern = Capec.query.filter_by(Capec_ID=selected_id).first()
            return render_template(f"home/{template}", segment=segment, data=selected_attack_pattern)
        
        elif template == 'threat-catalog.html':
            try:
                table = ThreatCatalog.query.all()
                if len(table) == 0:
                    table = None
            except:
                table = None
            return render_template(f"home/{template}", segment=segment, table=table)
        
        elif template == 'tools.html':
            try:
                table = ToolCatalog.query.all()
                if len(table) == 0:
                    table = None
            except:
                table = None
            return render_template(f"home/{template}", segment=segment, table=table)

        elif template == 'macm.html':
            try:
                table = Macm.query.all()
                if len(table) == 0:
                    table = None
            except:
                table = None
            try:
                attack_for_each_component = AttackView.query.with_entities(AttackView.Component_ID, func.count(AttackView.Component_ID)).group_by(AttackView.Component_ID).all()
                attack_for_each_component = converter.tuple_list_to_dict(attack_for_each_component)
            except:
                app.logger.error('Exception occurred while trying to serve ' + request.path, exc_info=True)
                attack_for_each_component = None
            return render_template(f"home/{template}", segment=segment, table=table, attack_for_each_component=attack_for_each_component)
        
        elif template == 'macm-detail.html':
            selected_id = request.args.get('id')
            macm_data = Macm.query.filter_by(Component_ID=selected_id).first()
            attack_data = AttackView.query.filter_by(Component_ID=selected_id).all()
            return render_template(f"home/{template}", segment=segment, macm_data=macm_data, attack_data=attack_data)

        # Serve the file (if exists) from app/templates/home/FILE.html
        return render_template(f"home/{template}", segment=segment)

    except TemplateNotFound:
        return render_template('home/page-404.html'), 404

    except:
        app.logger.error('Exception occurred while trying to serve ' + request.path, exc_info=True)
        return render_template('home/page-500.html'), 500

# Helper - Extract current page name from request
def get_segment(request):
    try:
        segment = request.path.split('/')[-1]
        if segment == '':
            segment = 'index'
        return segment
    except:
        return None
