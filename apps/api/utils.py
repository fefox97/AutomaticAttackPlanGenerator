import io
import os
from apps import db
from apps.databases.models import Capec, MacmUser, Macm, Attack
from flask import current_app as app
from sqlalchemy import or_, and_
import nmap as nm
import zipfile
import pandas as pd

from apps.my_modules.converter import Converter

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
    
    def query_to_excel(self, query_output, sheet_name):
        try:

            # Create a DataFrame using pd.DataFrame
            df = pd.DataFrame(query_output)

            file_bytes = io.BytesIO()
            with pd.ExcelWriter(file_bytes, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                
                # Get the xlsxwriter workbook and worksheet objects.
                workbook  = writer.book
                worksheet = writer.sheets[sheet_name]

                # Set the format for the columns
                wrap_format = workbook.add_format({'text_wrap': True})
                worksheet.set_column('A:B', 20, wrap_format) 
                worksheet.set_column('C:C', 10, wrap_format) 
                worksheet.set_column('D:D', 20, wrap_format) 
                worksheet.set_column('E:E', 40, wrap_format) 
                worksheet.set_column('F:F', 20, wrap_format)

                worksheet.freeze_panes(1, 0)

                writer.close()
            file_bytes.seek(0)
            return file_bytes
        
        except:
            app.logger.error(f"Error saving query to excel", exc_info=True)
            return None