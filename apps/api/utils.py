from apps import db
from apps.databases.models import Capec, MacmUser, Macm, ToolAssetRel
from flask import current_app as app
from sqlalchemy import or_, and_
import nmap as nm

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
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions
