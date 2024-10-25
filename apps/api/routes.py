# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

import json
from apps.api import blueprint
from flask import render_template, request, redirect, url_for, make_response
from flask_login import login_required, current_user
from jinja2 import TemplateNotFound
from flask import current_app as app
from flask import jsonify
from apps.my_modules import converter, macm, utils
from apps.api.utils import AttackPatternAPIUtils, APIUtils
from apps.databases.models import AttackView, Macm
from apps import db
import hashlib

@blueprint.route('/<api>', methods=['GET', 'POST'])
@login_required
def route_api(api):
    try:

        # Serve the api
        app.logger.info('Serving api ' + api)

        if request.method == 'POST':
                        
            if api == 'search_capec_by_id':
                search_id = request.form.get("SearchID") or ''
                showTree = True if request.form.get("ShowTree") == 'true' else False
                search_id_conv = converter.string_to_int_list(search_id)
                children = AttackPatternAPIUtils().get_child_attack_patterns(search_id_conv, show_tree=showTree)
                return jsonify({'children': children})
            
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
                if 'macmFile' in request.files and request.files['macmFile'].filename != '':
                    file = request.files['macmFile']
                    app.logger.info(f"Uploading MACM from file {request.files['macmFile']}")
                    if not APIUtils().allowed_file(file.filename, ['txt', 'macm']):
                        return make_response(jsonify({'message': 'File type not allowed'}), 400)
                    query_str = file.read().decode('utf-8')
                elif 'macmCypher' in request.form and request.form.get('macmCypher') != '':
                    query_str = request.form.get('macmCypher')
                else:
                    return make_response(jsonify({'message': 'No file or Cypher query provided'}), 400)
                try:
                    macm_db = f'db.{current_user.id}.{hashlib.sha1(query_str.encode("utf-8")).hexdigest()}'
                    macm.upload_macm(query_str, database=macm_db)
                    utils.upload_databases('Macm', neo4j_db=macm_db)
                    return make_response(jsonify({'message': 'MACM uploaded successfully'}), 200)
                except Exception as error:
                    return make_response(jsonify({'message': error.args}), 400)
            
            elif api == 'reload_databases':
                database = request.form.get('database')
                if database:
                    utils.upload_databases(database)
                    return make_response(jsonify({'message': f'Database {database} reloaded'}), 200)
                else:
                    return make_response(jsonify({'message': 'No database provided'}), 400)
            
            elif api == 'test':
                response = utils.test_function()
                return make_response(jsonify(response), 200)
    
            elif api == 'clear_macm':
                selected_macm = request.form.get('app-id')
                app.logger.info(f"Deleting MACM {selected_macm}")
                APIUtils.delete_macm(selected_macm)
                return redirect(url_for('home_blueprint.route_template', template='penetration-tests.html'))
            
            elif api == 'nmap_classic':
                # Get the file
                if 'outputFile' in request.files and request.files['outputFile'].filename != '':
                    file = request.files['outputFile']
                    if not APIUtils().allowed_file(file.filename, ['txt']):
                        return make_response(jsonify({'message': 'File type not allowed'}), 400)
                    output = file.read().decode('utf-8')
                    app.logger.info(output)
                    # Parse the output
                    return jsonify({'message': 'Nmap output parsed successfully', 'output': output})
                else:
                    return make_response(jsonify({'message': 'No file provided'}), 400)

    except Exception as e:
        app.logger.error('Exception occurred while trying to serve ' + request.path, exc_info=True)
        return render_template('home/page-500.html'), 500