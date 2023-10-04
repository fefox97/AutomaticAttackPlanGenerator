# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from apps.home import blueprint
from flask import render_template, request
from flask_login import login_required, current_user
from jinja2 import TemplateNotFound
from flask import current_app as app
from apps.databases.models import Capec, ThreatCatalog, Macm
from sqlalchemy.dialects import mysql

@blueprint.route('/index')
@login_required
def index():
    return render_template('home/dashboard.html', 
                            segment='dashboard', 
                            user_id=current_user.id)

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
            table = Capec.query.order_by(Capec.abstraction_order, Capec.Capec_ID).all()
            if len(table) == 0:
                table = None
            return render_template(f"home/{template}", segment=segment, table=table)

        elif template == 'capec-detail.html':
            selected_id = request.args.get('id')
            selected_attack_pattern = Capec.query.filter_by(Capec_ID=selected_id).first()
            return render_template(f"home/{template}", segment=segment, data=selected_attack_pattern)
        
        elif template == 'threat-catalog.html':
            table = ThreatCatalog.query.all()
            if len(table) == 0:
                table = None
            return render_template(f"home/{template}", segment=segment, table=table)
        
        elif template == 'macm.html':
            table = Macm.query.all()
            if len(table) == 0:
                table = None
            return render_template(f"home/{template}", segment=segment, table=table)
        
        elif template == 'macm-detail.html':
            selected_id = request.args.get('id')
            selected_macm = Macm.query.filter_by(Component_ID=selected_id).first()
            threat_catalog_data = ThreatCatalog.query.filter_by(Asset=selected_macm.Type).all()
            return render_template(f"home/{template}", segment=segment, macm_data=selected_macm, threat_catalog_data=threat_catalog_data)
        
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
