import io
import os
import re

from flask_login import current_user
from apps.celery_module.tasks import query_llm
from apps.databases.models import Capec, Settings
from apps.authentication.models import Tasks
from flask import current_app as app
from sqlalchemy import or_, and_
import zipfile
import pandas as pd
from bs4 import BeautifulSoup

from apps.my_modules.converter import Converter
from apps import db
import markdown2
from weasyprint import HTML

class AttackPatternAPIUtils:

    def get_child_attack_patterns_by_id(self, parent_id):
        try:
            return Capec.query.filter_by(Capec_ID=parent_id).first().Capec_Children_ID or []
        except:
            app.logger.error(f"Error getting children of {parent_id}", exc_info=True)
            return None

    def get_child_attack_patterns_recursive(self, parent_id) -> list:
        children = self.get_child_attack_patterns_by_id(parent_id)
        if children is None or len(children) == 0:
            return []
        else:
            for child in children:
                children = children + self.get_child_attack_patterns_recursive(child)
            return children

    def get_child_attack_patterns(self, parent_ids, show_tree=False):
        if type(parent_ids) is not list: parent_ids = [parent_ids]
        children = [parent_id for parent_id in parent_ids]
        if show_tree:
            children = children + [child for parent_id in parent_ids for child in self.get_child_attack_patterns_recursive(parent_id)]
        children = list(set(children))
        return children # return only the ids, not the dataframe
    
    def search_capec_by_keyword(self, search_keys, search_type):
        search_cols = [Capec.Name, Capec.Description, Capec.Extended_Description, Capec.Example_Instances, Capec.Execution_Flow]
        if search_type == 'and':
            search_args = [or_(and_(col.ilike(f"%{key}%") for key in search_keys) for col in search_cols)]
        else:
            search_args = [or_(col.ilike(f"%{key}%") for key in search_keys for col in search_cols)]
        query = Capec.query.filter(*search_args).with_entities(Capec.Capec_ID)
        output = query.all()
        # compiled = query.statement.compile(compile_kwargs={"literal_binds": True})
        # print(f"Query: {compiled}")
        # print(f"Output: {output}")
        return [x[0] for x in output]
    
class APIUtils:

    def __init__(self):
        self.converter = Converter()

    def allowed_file(self, filename, allowed_extensions):
        allowed_extensions = [x.replace('.', '') for x in allowed_extensions]
        if '*' in allowed_extensions:
            return True
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

    def delete_files(self, file_list):
        for file in file_list:
            try:
                os.remove(file)
            except:
                app.logger.error(f"Error deleting file {file}", exc_info=True)
                pass

    def zip_files(self, file_list, destinationpPath, zip_name):
        with zipfile.ZipFile(os.path.join(destinationpPath, zip_name), 'w') as zipf:
            for file in file_list:
                zipf.write(file, os.path.basename(file))
        return f"{destinationpPath}/{zip_name}"

    def query_to_excel(self, query_output, sheet_name, column_format=None, html_columns=None):
        try:

            # Create a DataFrame using pd.DataFrame
            df = pd.DataFrame(query_output)

            if html_columns is not None:
                for col in html_columns:
                    df[col] = df[col].apply(lambda x: BeautifulSoup(x, features="html.parser").get_text('\n') if x is not None else x)

            file_bytes = io.BytesIO()
            with pd.ExcelWriter(file_bytes, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                
                # Get the xlsxwriter workbook and worksheet objects.
                workbook  = writer.book
                worksheet = writer.sheets[sheet_name]

                # Set the format for the columns
                wrap_format = workbook.add_format({'text_wrap': True})
                if column_format is not None:
                    for col, fmt in column_format.items():
                        worksheet.set_column(fmt['columns'], fmt['width'], wrap_format)

                worksheet.freeze_panes(1, 0)

                writer.close()
            file_bytes.seek(0)
            return file_bytes
        
        except:
            app.logger.error(f"Error saving query to excel", exc_info=True)
            return None
    
    def query_to_json(self, query_output, html_columns=None):
        try:
            df = pd.DataFrame(query_output)

            if html_columns is not None:
                for col in html_columns:
                    df[col] = df[col].apply(lambda x: BeautifulSoup(x, features="html.parser").get_text('\n') if x is not None else x)
            return df.to_json(orient='index')
        
        except:
            app.logger.error(f"Error converting query to json", exc_info=True)
            return None
    
    def generate_pentest_report(self, app_id):
        try:
            report = query_llm.delay(app_id)
            task = Tasks(
                id=report.id,
                name="Pentest report generation",
                app_id=app_id,
                user_id=current_user.id,
            )
            db.session.add(task)
            db.session.commit()
            return True
        except:
            app.logger.error(f"Error making the request to LLM", exc_info=True)
            return None

    def download_pentest_report(self, app_name, content):
        try:
            content = f"# 📄 {app_name} Pentest Report\n" + content
            body = markdown2.markdown(content)
            filebytes = io.BytesIO()
            HTML(string=body).write_pdf(filebytes, stylesheets=[app.config['PENTEST_REPORT_CSS']])
            filebytes.seek(0)
            return filebytes
        except Exception as e:
            app.logger.error(f"Error making the request to LLM: {e}", exc_info=True)
            return None