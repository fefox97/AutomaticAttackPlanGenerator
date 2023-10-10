# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

import json
from apps.api import blueprint
from flask import render_template, request, redirect, url_for
from flask_login import login_required, current_user
from jinja2 import TemplateNotFound
from flask import current_app as app
from flask import jsonify
from apps.my_modules import converter, macm, utils
from apps.api.utils import AttackPatternAPIUtils, APIUtils
from apps.databases.models import AttackView, Macm
from apps import db

# @login_required
@blueprint.route('/<api>', methods=['GET', 'POST'])
def route_api(api):
    try:

        # Serve the api
        app.logger.info('Serving api ' + api)

        if request.method == 'POST':
                        
            if api == 'search_capec_by_id':
                search_id = request.form.get("SearchID") or ''
                showTree = True if request.form.get("ShowTree") == 'true' else False
                search_id_conv = converter.string_to_int_list(search_id)
                childs = AttackPatternAPIUtils().get_child_attack_patterns(search_id_conv, show_tree=showTree)
                return jsonify({'childs': childs})
            
            elif api == 'search_capec_by_keyword':
                search_keys = request.form.get("SearchKeyword")
                search_type = request.form.get("SearchType")
                if search_keys is None:
                    return jsonify({'ids': []})
                search_keys = json.loads(search_keys)
                app.logger.info(f"Searching for {search_keys} with type {search_type}")
                result = AttackPatternAPIUtils().search_capec_by_keyword(search_keys, search_type)
                return jsonify({'ids': result})

            elif api == 'upload_macm':
                if 'macmFile' in request.files:
                    file = request.files['macmFile']
                    if not APIUtils().allowed_file(file.filename, ['txt', 'macm']):
                        return jsonify({'success': False, 'message': 'File type not allowed'})
                    query_str = file.read().decode('utf-8')
                elif 'macmCypher' in request.form:
                    query_str = request.form.get('macmCypher')
                else:
                    return jsonify({'success': False, 'message': 'No file or Cypher query provided'})
                macm.upload_macm(query_str)
                utils.upload_databases('Macm')
                return redirect(url_for('home_blueprint.route_template', template='macm.html'))
            
            elif api == 'reload_databases':
                database = request.form.get('database')
                if database:
                    utils.upload_databases(database)
                return jsonify({'success': True, 'message': f'Database {database} reloaded'})
            
            elif api == 'test':
                utils.test_function()
                return jsonify({'success': True, 'message': 'Test successful'})
        
        elif request.method == 'GET':
            if api == 'clear_macm_database':
                macm.clear_database('macm')
                db.session.query(Macm).delete()
                db.session.commit()
                return redirect(url_for('home_blueprint.route_template', template='macm.html'))

    except:
        app.logger.error('Exception occurred while trying to serve ' + request.path, exc_info=True)
        return render_template('home/page-500.html'), 500