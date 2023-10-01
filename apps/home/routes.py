# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from apps.home import blueprint
from flask import render_template, request
from flask_login import login_required, current_user
from jinja2 import TemplateNotFound
from flask import current_app as app
from flask import jsonify
from apps.my_modules import converter, attack_pattern, threat_catalog, macm
from werkzeug.utils import secure_filename
from apps import utils


@blueprint.route('/index')
@login_required
def index():

    return render_template('home/dashboard.html', 
                            segment='dashboard', 
                            user_id=current_user.id)

# @login_required
@blueprint.route('/<template>', methods=['GET', 'POST'])
def route_template(template):

    try:

        if not template.endswith('.html'):
            template += '.html'

        # Detect the current page
        segment = get_segment(request)
        app.logger.info('Serving ' + template)

        # Serve the file (if exists) from app/templates/home/FILE.html
        if template == 'capec.html':
            df = attack_pattern.attack_pattern_df
            app.logger.info(f"Childs ID of 607: {df.loc[607].get('Capec Childs ID')}")
            if request.method == 'POST':
                search_id = request.form.get("SearchID") or ''
                showTree = True if request.form.get("ShowTree") == 'true' else False
                search_id_conv = converter.string_to_int_list(search_id)
                childs = attack_pattern.get_child_attack_patterns(search_id_conv, df, show_tree=showTree)
                app.logger.info(f"Searched Childs ID: {childs}")
                return jsonify({'childs': childs})
            
            df = converter.capec_abstraction_sort(df)
            if df is not None:
                df_html = converter.attack_pattern_to_html(df, classes='table table-striped table-hover table-dataframe', table_id='capec_table', escape=False)
            return render_template(f"home/{template}", segment=segment, table=df_html)

        elif template == 'capec-detail.html':
            selected_id = request.args.get('id')
            df = attack_pattern.attack_pattern_df
            selected_attack_pattern = df.loc[int(selected_id)]
            app.logger.info(f"Searched Childs ID: {selected_attack_pattern['Capec Childs ID']}")
            return render_template(f"home/{template}", segment=segment, data=selected_attack_pattern)
        
        elif template == 'threat-catalog.html':
            df = threat_catalog.threat_catalog_df
            if df is not None:
                df_html = converter.threat_catalog_to_html(df, classes='table table-striped table-hover table-dataframe', table_id='threat_catalog_table', escape=False)
            return render_template(f"home/{template}", segment=segment, table=df_html)
        
        elif template == 'macm.html':
            if request.method == 'POST':
                if 'macmFile' in request.files:
                    file = request.files['macmFile']
                    if not utils.allowed_file(file.filename, 'txt'):
                        return jsonify({'success': False, 'message': 'File type not allowed'})
                    query_str = file.read().decode('utf-8')
                elif 'macmCypher' in request.form:
                    query_str = request.form.get('macmCypher')
                else:
                    return jsonify({'success': False, 'message': 'No file or Cypher query provided'})
                macm.upload_macm(query_str)
            df = macm.read_macm()
            if df is not None:
                df_html = converter.macm_to_html(df, classes='table table-striped table-hover table-dataframe', table_id='macm_table', escape=False)
            return render_template(f"home/{template}", segment=segment, table=df_html)

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
