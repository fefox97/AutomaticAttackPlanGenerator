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
from apps.my_modules import converter, attack_pattern, threat_catalog
from flask_modals import render_template_modal


@blueprint.route('/index')
@login_required
def index():

    return render_template('home/dashboard.html', 
                            segment='dashboard', 
                            user_id=current_user.id)

@blueprint.route('/<template>', methods=['GET', 'POST'])
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
            df = attack_pattern.attack_pattern_df
            if request.method == 'POST':
                search_id = request.form.get("SearchID") or ''
                showTree = True if request.form.get("ShowTree") == 'true' else False
                search_id_conv = converter.string_to_int_list(search_id)
                childs = attack_pattern.get_child_attack_patterns(search_id_conv, df, show_tree=showTree)
                return jsonify({'childs': childs})
            
            df = converter.capec_abstraction_sort(df)
            if df is not None:
                df_html = converter.attack_pattern_to_html(df, classes='table table-striped table-hover table-dataframe', table_id='capec_table', escape=False)
            return render_template("home/" + template, segment=segment, table=df_html)

        elif template == 'capec-detail.html':
            selected_id = request.args.get('id')
            df = attack_pattern.attack_pattern_df
            selected_attack_pattern = df.loc[int(selected_id)]
            # return render_template("home/" + template, segment=segment, data=selected_attack_pattern)
            return render_template_modal("home/capec-detail-modal.html", segment=segment, data=selected_attack_pattern)
        
        elif template == 'threat-catalog.html':
            df = threat_catalog.threat_catalog_df
            if df is not None:
                df_html = converter.threat_catalog_to_html(df, classes='table table-striped table-hover table-dataframe', table_id='threat_catalog_table', escape=False)
            return render_template("home/" + template, segment=segment, table=df_html)

        # Serve the file (if exists) from app/templates/home/FILE.html
        return render_template("home/" + template, segment=segment)

    except TemplateNotFound:
        return render_template('home/page-404.html'), 404

    except:
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
