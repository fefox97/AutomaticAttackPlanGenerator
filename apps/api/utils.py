from apps import db
from apps.databases.models import Capec, MacmUser, Macm, ToolAssetRel
from flask import current_app as app
from sqlalchemy import or_, and_

from apps.my_modules.utils import MacmUtils

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

    def allowed_file(self, filename, allowed_extensions):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions
    
    def delete_macm(app_id):
        try:
            Macm.query.filter_by(App_ID=app_id).delete()
            MacmUser.query.filter_by(AppID=app_id).delete()
            ToolAssetRel.query.filter_by(AppID=app_id).delete()
            MacmUtils().delete_database(app_id)
            db.session.commit()
            return True
        except:
            app.logger.error(f"Error deleting MACM {app_id}", exc_info=True)
            return False