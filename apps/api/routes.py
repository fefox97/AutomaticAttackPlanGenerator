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
from apps.api.parser import NmapParser
from apps.databases.models import AttackView, Macm, ToolCatalogue
from apps import db
import hashlib

@blueprint.route('/search_capec_by_id', methods=['POST'])
def search_capec_by_id():
    search_id = request.form.get("SearchID") or ''
    showTree = True if request.form.get("ShowTree") == 'true' else False
    search_id_conv = converter.string_to_int_list(search_id)
    children = AttackPatternAPIUtils().get_child_attack_patterns(search_id_conv, show_tree=showTree)
    return jsonify({'children': children})

@blueprint.route('/search_capec_by_keyword', methods=['POST'])
def search_capec_by_keyword():
    search_keys = request.form.get("SearchKeyword")
    search_type = request.form.get("SearchType")
    if search_keys is None:
        return jsonify({'ids': []})
    search_keys = json.loads(search_keys)
    app.logger.info(f"Searching for {search_keys} with type {search_type}")
    result = AttackPatternAPIUtils().search_capec_by_keyword(search_keys, search_type)
    return jsonify({'ids': result})

@blueprint.route('/upload_macm', methods=['POST'])
def upload_macm():
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

@blueprint.route('/update_macm', methods=['POST'])
def update_macm():
    app_id = request.form.get('AppID')
    query = request.form.get('QueryCypher')
    if app_id:
        try:
            app.logger.info(f"Updating MACM {app_id} with query {query}")
            macm.update_macm(query, app_id)
            return make_response(jsonify({'message': 'MACM updated successfully'}), 200)
        except Exception as error:
            return make_response(jsonify({'message': error.args}), 400)
    else:
        return make_response(jsonify({'message': 'No MACM provided'}), 400)

@blueprint.route('/delete_macm_component', methods=['POST'])
def delete_macm_component():
    app_id = request.form.get('AppID')
    component_id = request.form.get('ComponentID')
    if app_id and component_id:
        try:
            app.logger.info(f"Deleting component {component_id} from MACM {app_id}")
            macm.delete_macm_component(app_id, component_id)
            return make_response(jsonify({'message': 'Component deleted successfully'}), 200)
        except Exception as error:
            return make_response(jsonify({'message': error.args}), 400)
    else:
        return make_response(jsonify({'message': 'No MACM or component provided'}), 400)

@blueprint.route('/reload_databases', methods=['POST'])
def reload_databases():
    database = request.form.get('database')
    if database:
        utils.upload_databases(database)
        return make_response(jsonify({'message': f'Database {database} reloaded'}), 200)
    else:
        return make_response(jsonify({'message': 'No database provided'}), 400)

@blueprint.route('/test', methods=['GET', 'POST'])
def test():
    response = utils.test_function()
    return make_response(jsonify(response), 200)

@blueprint.route('/clear_macm', methods=['POST'])
def clear_macm():
    selected_macm = request.form.get('deleteAppID')
    app.logger.info(f"Deleting MACM {selected_macm}")
    macm.delete_macm(selected_macm)
    return redirect(url_for('home_blueprint.route_template', template='penetration-tests.html'))
    
@blueprint.route('/nmap_classic', methods=['GET', 'POST'])
def nmap_classic():
    if 'outputFile' in request.files and request.files['outputFile'].filename != '':
        file = request.files['outputFile']
        allowed_extensions = ToolCatalogue.query.filter_by(OutputParser='nmap_classic').first().AllowedOutputExtensions
        if not APIUtils().allowed_file(file.filename, allowed_extensions):
            return make_response(jsonify({'message': 'File type not allowed'}), 400)
        content = file.read().decode('utf-8')
        # Parse the output
        output = NmapParser().nmap_classic(request.form.get('macmID'), content)
        return jsonify({'message': 'Nmap output parsed successfully', 'output': output})
    else:
        return make_response(jsonify({'message': 'No file provided'}), 400)