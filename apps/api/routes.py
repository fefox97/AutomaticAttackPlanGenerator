import os
import datetime
import json
import traceback
import uuid

from atlassian import Jira
from sqlalchemy import select
from apps.api import blueprint
from flask import render_template_string, request, send_file, make_response
from flask_security import auth_required, current_user, roles_required
from flask import current_app as app
from flask import jsonify
from apps.authentication.models import Tasks
from apps.celery_module.tasks import retrieve_wiki_pages
from apps.my_modules import converter, macm, utils
from apps.api.utils import AttackPatternAPIUtils, APIUtils
from apps.api.parser import NmapParser
from apps.databases.models import App, Attack, AttackView, Settings, ThreatModel, ToolCatalogue
from apps import db, mail
from sqlalchemy.sql.expression import null
from celery.result import AsyncResult

from apps.templates.security.email.report_issue import report_issue_html_content

from github import Github
import os

@auth_required
@blueprint.route('/get_pending_tasks', methods=['GET'])
def get_pending_tasks():
    pentest_report_tasks_query = select(Tasks.id,
                    Tasks.name,
                    Tasks.type,
                    Tasks.app_id,
                    Tasks.created_on,
                    App.Name.label('app_name')
                    ).select_from(Tasks).filter_by(user_id=current_user.id, type='pentest_report').join(App, App.AppID == Tasks.app_id)
    wiki_pages_retrieval_tasks_query = select(Tasks.id,
                            Tasks.name,
                            Tasks.type,
                            Tasks.created_on
                        ).filter_by(user_id=current_user.id, type='wiki_pages_retrieval')
    pentest_report_tasks = db.session.execute(pentest_report_tasks_query).fetchall()
    wiki_pages_retrieval_tasks = db.session.execute(wiki_pages_retrieval_tasks_query).fetchall()

    # Unify all tasks in a single list
    all_tasks = []
    for task in pentest_report_tasks:
        all_tasks.append({
            'task_id': task.id,
            'task_name': task.name,
            'type': task.type,
            'app_id': task.app_id,
            'app_name': task.app_name,
            'created_on': task.created_on,
        })
    for task in wiki_pages_retrieval_tasks:
        all_tasks.append({
            'task_id': task.id,
            'task_name': task.name,
            'type': task.type,
            'created_on': task.created_on,
            'app_id': None,
            'app_name': None,
        })

    return jsonify({'tasks': all_tasks})

@auth_required
@blueprint.route('/get_task_status', methods=['POST'])
def get_task_status():
    task_id = request.form.get("task_id")
    task_result = AsyncResult(task_id)
    result = {
        "task_id": task_id,
        "task_status": task_result.status,
        "task_result": task_result.result
    }
    if type(task_result.result) is Exception:
        result['task_result'] = task_result.result.args
    return jsonify(result)

@auth_required
@blueprint.route('/delete_task', methods=['POST'])
def delete_task():
    task_id = request.form.get("task_id")
    task = Tasks.query.filter_by(id=task_id).first()
    if task is not None:
        db.session.delete(task)
        db.session.commit()
        return jsonify({'message': 'Task deleted'})
    else:
        return jsonify({'message': 'Task not found'}), 404

@auth_required
@blueprint.route('/search_capec_by_id', methods=['POST'])
def search_capec_by_id():
    search_id = request.form.get("SearchID") or ''
    showTree = True if request.form.get("ShowTree") == 'true' else False
    search_id_conv = converter.string_to_int_list(search_id)
    children = AttackPatternAPIUtils().get_child_attack_patterns(search_id_conv, show_tree=showTree)
    return jsonify({'children': children})

@auth_required
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

@auth_required
@blueprint.route('/upload_macm', methods=['POST'])
def upload_macm():
    app_name = request.form.get('macmAppName')
    if app_name in [None, '']:
        return make_response(jsonify({'message': 'No App Name provided'}), 400)
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
        macm_db = f'db.{current_user.id}.{uuid.uuid4()}'
        macm.upload_macm(query_str, app_name=app_name, database=macm_db)
        return make_response(jsonify({'message': 'MACM uploaded successfully'}), 200)
    except Exception as error:
        app.logger.error(f"Error uploading MACM: {error.args}", exc_info=True)
        return make_response(jsonify({'message': error.args}), 400)

@auth_required
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

@auth_required
@blueprint.route('/rename_macm', methods=['POST'])
def rename_macm():
    app_id = request.form.get('AppID')
    new_name = request.form.get('AppName')
    if new_name in [None, '']:
        return make_response(jsonify({'message': 'No App Name provided'}), 400)
    if app_id:
        try:
            app.logger.info(f"Renaming MACM {app_id} to {new_name}")
            macm.rename_macm(app_id, new_name)
            return make_response(jsonify({'message': 'MACM renamed successfully'}), 200)
        except Exception as error:
            return make_response(jsonify({'message': error.args}), 400)
    else:
        return make_response(jsonify({'message': 'No MACM provided'}), 400)

@auth_required
@blueprint.route('/delete_macm', methods=['POST'])
def clear_macm():
    selected_macm = request.form.get('AppID')
    app.logger.info(f"Deleting MACM {selected_macm}")
    try:
        macm.delete_macm(selected_macm)
        return make_response(jsonify({'message': 'MACM deleted successfully'}), 200)
    except Exception as error:
        return make_response(jsonify({'message': error.args}), 400)

@auth_required
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

@auth_required
@blueprint.route('/share_macm', methods=['POST'])
def share_macm():
    app_id = request.form.get('AppID')
    users = request.form.get('Users')
    if app_id:
        try:
            app.logger.info(f"Sharing MACM {app_id} with user {users}")
            macm.share_macm(app_id, users)
            return make_response(jsonify({'message': 'MACM shared successfully'}), 200)
        except Exception as error:
            return make_response(jsonify({'message': error.args}), 400)
    else:
        return make_response(jsonify({'message': 'No MACM provided'}), 400)

@auth_required
@blueprint.route('/unshare_macm', methods=['POST'])
def unshare_macm():
    app_id = request.form.get('AppID')
    user_id = request.form.get('UserID')
    if app_id:
        try:
            app.logger.info(f"Unsharing MACM {app_id} for user {user_id}")
            macm.unshare_macm(app_id, user_id)
            return make_response(jsonify({'message': 'MACM unshared successfully'}), 200)
        except Exception as error:
            return make_response(jsonify({'message': error.args}), 400)
    else:
        return make_response(jsonify({'message': 'No MACM provided'}), 400)

@auth_required
@blueprint.route('/reload_databases', methods=['POST'])
def reload_databases():
    database = request.form.get('database')
    try:
        if database:
            utils.upload_databases(database)
            return make_response(jsonify({'message': f'Database {database} reloaded'}), 200)
        else:
            return make_response(jsonify({'message': 'No database provided'}), 400)
    except Exception as error:
        return make_response(jsonify({'message': error.args}), 400)

@auth_required
@blueprint.route('/test', methods=['GET', 'POST'])
def test():
    response = utils.test_function()
    return make_response(jsonify(response), 200)

@auth_required
@blueprint.route('/upload_excel', methods=['POST'])
def upload_excel():
    if 'file' in request.files and request.files['file'].filename != '':
        file = request.files['file']
        app.logger.info(f"Uploading Excel from file {file.filename}")
        if not APIUtils().allowed_file(file.filename, ['xlsx', 'xls', 'xlsm']):
            return make_response(jsonify({'message': 'File type not allowed'}), 400)
        try:
            filename = file.filename
            path = app.config["DBS_PATH"]
            file.save(f'{path}/{filename}')
            catalogs_filename = Settings.query.filter_by(key='catalogs_filename').first()
            old_filename = catalogs_filename.value if catalogs_filename else None
            if catalogs_filename:
                catalogs_filename.value = filename
            else:
                catalogs_filename = Settings(key='catalogs_filename', value=filename)
                db.session.add(catalogs_filename)
            db.session.commit()
            # Cancella il vecchio file se esiste e il nome è diverso
            if old_filename and old_filename != filename:
                old_file_path = os.path.join(path, old_filename)
                try:
                    if os.path.exists(old_file_path):
                        os.remove(old_file_path)
                except Exception as e:
                    app.logger.warning(f"Impossibile cancellare il vecchio file catalogo: {e}")
            return make_response(jsonify({'message': 'Excel uploaded successfully', 'filename': filename}), 200)
        except Exception as error:
            return make_response(jsonify({'message': error.args}), 400)
    else:
        return make_response(jsonify({'message': 'No file provided'}), 400)

@auth_required
@blueprint.route('/download_excel', methods=['POST'])
def download_excel():
    filename = Settings.query.filter_by(key='catalogs_filename').first().value
    path = app.config["DBS_PATH"]
    return send_file(f'{path}/{filename}', as_attachment=True, mimetype='application/octet-stream', download_name=filename)

@auth_required
@blueprint.route('/download_threat_model', methods=['POST'])
def download_threat_model():
    app_id = request.form.get('AppID')
    try:
        app_name = App.query.filter_by(AppID=app_id).with_entities(App.Name).first()[0]
        threat_model = ThreatModel.query.filter_by(AppID=app_id).with_entities(
            ThreatModel.Asset,
            ThreatModel.Asset_Type.label('Asset Type'),
            ThreatModel.Threat_ID.label('Threat ID'),
            ThreatModel.Threat,
            ThreatModel.Threat_Description.label('Threat Description'),
            ThreatModel.Compromised,
            ThreatModel.PreC,
            ThreatModel.PreI,
            ThreatModel.PreA,
            ThreatModel.PostC,
            ThreatModel.PostI,
            ThreatModel.PostA,
            ThreatModel.STRIDE).all()
        if threat_model is None:
            raise Exception(f"Threat model not found for MACM {app_name}")
        column_format = {
            1: {'columns': 'A:B', 'width': 20},
            2: {'columns': 'C:C', 'width': 10},
            3: {'columns': 'D:D', 'width': 20},
            4: {'columns': 'E:E', 'width': 40},
            5: {'columns': 'F:F', 'width': 20}
        }
        excel_file = APIUtils().query_to_excel(threat_model, 'Threat Model', column_format)
        return send_file(excel_file, as_attachment=True, mimetype='application/octet-stream', download_name=f"{app_name}_threat_model.xlsx")
    except Exception as error:
        app.logger.info(f"Error downloading threat model for MACM {app_id}:\n {error}")
        return make_response(jsonify({'message': error.args}), 400)

@auth_required
@blueprint.route('/download_attack_plan', methods=['POST'])
def download_attack_plan():
    app_id = request.form.get('AppID')
    try:
        app_name = App.query.filter_by(AppID=app_id).with_entities(App.Name).first()[0]
        attack_plan = AttackView.query.filter_by(AppID=app_id).with_entities(
            AttackView.Attack_Number.label('Attack Number'),
            AttackView.Component_ID.label('Component ID'),
            AttackView.Asset,
            AttackView.Asset_Type.label('Asset Type'),
            AttackView.Threat_ID.label('Threat ID'),
            AttackView.Threat,
            AttackView.Threat_Description.label('Threat Description'),
            AttackView.PhaseName.label('Phase'),
            AttackView.Capec_ID.label('CAPEC ID'),
            AttackView.Attack_Pattern.label('Attack Pattern'),
            AttackView.Capec_Description.label('CAPEC Description'),
            AttackView.Execution_Flow.label('Execution Flow'),
            AttackView.Tool_ID.label('Tool ID'),
            AttackView.Tool_Name.label('Tool Name'),
            AttackView.Tool_Description.label('Tool Description'),
            AttackView.Command,
            ).all()
        if attack_plan is None:
            raise Exception(f"Attack Plan not found for MACM {app_name}")
        
        column_format = {
            1: {'columns': 'A:B', 'width': 12},
            2: {'columns': 'C:C', 'width': 15},
            3: {'columns': 'D:D', 'width': 20},
            4: {'columns': 'F:F', 'width': 20},
            5: {'columns': 'G:G', 'width': 40},
            6: {'columns': 'H:H', 'width': 30},
            7: {'columns': 'J:J', 'width': 20},
            8: {'columns': 'K:K', 'width': 40},
            9: {'columns': 'L:L', 'width': 120},
            10: {'columns': 'N:N', 'width': 10},
            11: {'columns': 'O:P', 'width': 40},
        }

        excel_file = APIUtils().query_to_excel(attack_plan, 'Attack Plan', column_format, ['Execution Flow'])
        return send_file(excel_file, as_attachment=True, mimetype='application/octet-stream', download_name=f"{app_name}_attack_plan.xlsx")
    except Exception as error:
        app.logger.info(f"Error downloading the Attack Plan for MACM {app_id}:\n {error}")
        return make_response(jsonify({'message': error.args}), 400)

@auth_required
@blueprint.route('/generate_ai_report', methods=['POST'])
def generate_ai_report():
    app_id = request.form.get('AppID')
    try:
        if Tasks.query.filter_by(app_id=app_id, user_id=current_user.id).first() is not None:
                return make_response(jsonify({'message': 'Report already in progress or completed. Check the notifications to download the report.'}), 400)

        app_name = App.query.filter_by(AppID=app_id).with_entities(App.Name).first()[0]

        APIUtils().generate_pentest_report(app_id)
        return jsonify({'message': 'Report generation started'})
    except Exception as error:
        app.logger.info(f"Error generating the report for MACM {app_id}:\n {error}")
        return make_response(jsonify({'message': error.args}), 400)

@auth_required
@blueprint.route('/download_ai_report', methods=['POST'])
def download_ai_report():
    app_id = request.form.get('AppID')
    task_id = request.form.get('TaskID')
    try:
        task_result = AsyncResult(task_id)
        app_name = App.query.filter_by(AppID=app_id).with_entities(App.Name).first()[0]
        if task_result is None or task_result.status != 'SUCCESS':
            return jsonify({'message': 'Task not found'}), 404
        report_file = APIUtils().download_pentest_report(app_name, task_result.result)
        return send_file(report_file, as_attachment=True, mimetype='application/octet-stream', download_name=f"{app_name}_report.pdf")
    except Exception as error:
        app.logger.info(f"Error downloading the report for MACM {app_id}:\n {error}")
        return make_response(jsonify({'message': error.args}), 400)

@auth_required
@blueprint.route('/upload_report', methods=['POST'])
def upload_report():
    if 'reportFile' in request.files and request.files['reportFile'].filename != '':
        file = request.files['reportFile']
        macmID = request.form.get('macmID')
        componentID = request.form.get('componentID')
        toolID = request.form.get('toolID')
        filename = f"{current_user.id}_{componentID}_{toolID}_{file.filename}"
        path = f'{app.config["UPLOAD_FOLDER"]}'
        allowed_extensions = ToolCatalogue.query.filter_by(ToolID=toolID).first().AllowedReportExtensions
        if not APIUtils().allowed_file(file.filename, allowed_extensions):
            return make_response(jsonify({'message': 'File type not allowed'}), 400)

        try:
            currentReport = Attack.query.filter_by(AppID=macmID, ComponentID=componentID, ToolID=toolID).first()
            if currentReport is not None and currentReport.ReportFiles is not None and 'path' in currentReport.ReportFiles:
                oldPath = currentReport.ReportFiles['path']
                APIUtils().delete_files([oldPath])
            currentReport.ReportFiles = {
                'filename': filename,
                'path': path
            }
            file.save(f'{path}/{filename}')
            db.session.commit()
            return jsonify({'message': 'File uploaded successfully'})
        except Exception as error:
                traceback.print_exc()
                return make_response(jsonify({'message': error.args}), 400)
    else:
        app.logger.error('No file provided')
        return make_response(jsonify({'message': 'No file provided'}), 400)

@auth_required
@blueprint.route('/delete_report', methods=['POST'])
def delete_report():
    macmID = request.form.get('macmID')
    componentID = request.form.get('componentID')
    toolID = request.form.get('toolID')
    try:
        currentReport = Attack.query.filter_by(AppID=macmID, ComponentID=componentID, ToolID=toolID).first()
        if currentReport is not None and currentReport.ReportFiles is not None and 'path' in currentReport.ReportFiles:
            oldPath = currentReport.ReportFiles['path']
            filename = currentReport.ReportFiles['filename']
            APIUtils().delete_files([f'{oldPath}/{filename}'])
            # null the report files
            currentReport.ReportFiles = null()
            db.session.commit()
            return jsonify({'message': 'File deleted successfully'})
        else:
            return jsonify({'message': 'No file to delete'})
    except Exception as error:
        traceback.print_exc()
        return make_response(jsonify({'message': error.args}), 400)

@auth_required
@blueprint.route('/download_report', methods=['POST'])
def download_report():
    macmID = request.form.get('macmID')
    componentID = request.form.get('componentID')
    toolID = request.form.get('toolID')
    try:
        path = Attack.query.filter_by(AppID=macmID, ComponentID=componentID, ToolID=toolID).first().ReportFiles['path']
        filename = Attack.query.filter_by(AppID=macmID, ComponentID=componentID, ToolID=toolID).first().ReportFiles['filename']
        return send_file(f'{path}/{filename}', as_attachment=True, mimetype='application/octet-stream', download_name=filename)
    except Exception as error:
        traceback.print_exc()
        return make_response(jsonify({'message': error.args}), 400)

@auth_required
@blueprint.route('/download_all_reports', methods=['POST'])
def download_all_reports():
    macmID = request.form.get('macmID')
    try:
        reports = Attack.query.filter_by(AppID=macmID).where(Attack.ReportFiles.isnot(None)).distinct().all()
        destinationPath = app.config["TMP_FOLDER"]
        filenames = [f"{report.ReportFiles['path']}/{report.ReportFiles['filename']}" for report in reports]
        if len(filenames) == 0:
            return make_response(jsonify({'message': 'No reports to download'}), 400)
        zip_filename = f'{macmID}_reports.zip'
        zip_filename = APIUtils().zip_files(filenames, destinationPath, zip_filename)
        return send_file(zip_filename, as_attachment=True, mimetype='application/octet-stream', download_name=f'{macmID}_reports.zip')
    except Exception as error:
        traceback.print_exc()
        return make_response(jsonify({'message': error.args}), 400)

@auth_required
@blueprint.route('/nmap/<string:parser>', methods=['POST'])
def nmap(parser):
    macmID = request.form.get('macmID')
    componentID = request.form.get('componentID')
    toolID = request.form.get('toolID')
    path = Attack.query.filter_by(AppID=macmID, ComponentID=componentID, ToolID=toolID).first().ReportFiles['path']
    filename = Attack.query.filter_by(AppID=macmID, ComponentID=componentID, ToolID=toolID).first().ReportFiles['filename']
    try:
        with open(f'{path}/{filename}', 'rb') as file:
            content = file.read().decode('utf-8')
            # Parse the output
            output = getattr(NmapParser(), f'nmap_{parser}')(request.form.get('macmID'), request.form.get('componentID'), content)
            return jsonify({'message': 'Nmap output parsed successfully', 'output': output})
    except Exception as error:
        traceback.print_exc()
        return make_response(jsonify({'message': error.args}), 400)

@auth_required
@roles_required('admin')
@blueprint.route('/ticket', methods=['POST'])
def ticket():
    jira = Jira(url=app.config['JIRA_URL'], username=app.config['JIRA_USERNAME'], password=app.config['JIRA_API_KEY'], cloud=True)
    issue = request.form.get('issue')
    subject = request.form.get('subject')
    email = request.form.get('email')
    date = datetime.datetime.now().strftime('%Y-%m-%d')
    app.logger.info(f"Creating Jira issue with subject {subject} and issue {issue}")
    try:
        new_issue = jira.issue_create(
            fields={
                'project': {'key': app.config['JIRA_PROJECT']},
                'summary': subject,
                'description': issue,
                'customfield_10037': email,
                'customfield_10038': date,
                'issuetype': {'name': app.config['JIRA_TICKET_TYPE']}
            }
        )
        app.logger.info(f"Jira issue created with ID {new_issue['key']}")
    except Exception as error:
        app.logger.error(f"Error creating Jira issue: {error.args}", exc_info=True)
        return make_response(jsonify({'message': error.args}), 400)
    return make_response(jsonify({'message': 'Report created successfully with ID ' + new_issue['key']}), 200)

@auth_required
@blueprint.route('/issue', methods=['POST'])
def issue():
    try:
        issue = request.form.get('issue')
        subject = request.form.get('subject')
        email = request.form.get('email')
        email_body = render_template_string(report_issue_html_content, subject=subject, user_email=email, issue=issue)
        mail.send_mail(
            from_email=app.config["MAIL_DEFAULT_SENDER"],
            subject=f"Issue from {email}",
            recipient_list=['issues@vseclab.it'],
            message=email_body,
            html_message=email_body,
        )
    except Exception as error:
        app.logger.error(f"Error sending issue: {error.args}", exc_info=True)
        return make_response(jsonify({'message': error.args}), 400)
    return make_response(jsonify({'message': 'Report created successfully'}), 200)

@auth_required
@blueprint.route('/edit_setting', methods=['POST'])
def edit_setting():
    key = request.form.get('key')
    value = request.form.get('value')
    try:
        Settings.query.filter_by(key=key).update({'value': value})
        db.session.commit()
        return make_response(jsonify({'message': 'Setting updated successfully'}), 200)
    except Exception as error:
        app.logger.error(f"Error editing setting: {error.args}", exc_info=True)
        return make_response(jsonify({'message': error.args}), 400)
    
@auth_required
@roles_required('admin')
@blueprint.route('/retrieve_wiki', methods=['GET'])
def get_wiki():
    repo_url = app.config['WIKI_REPO']
    wiki_folder = app.config['FLATPAGES_ROOT']
    try:
        pages = APIUtils().retrieve_wiki_pages(wiki_repo_url=repo_url, wiki_folder=wiki_folder)
        return jsonify({'message': "Wiki pages retrieve started successfully"})
    except Exception as error:
        app.logger.error(f"Error retrieving wiki: {error.args}", exc_info=True)
        return make_response(jsonify({'message': error.args}), 400)