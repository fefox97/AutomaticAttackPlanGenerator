from apps import db
from apps.databases.models import Capec
from flask import current_app as app

class AttackPatternAPIUtils:

    def get_child_attack_patterns_by_id(self, parent_id):
        try:
            return Capec.query.filter_by(Capec_ID=parent_id).first().Capec_Childs_ID or []
        except:
            app.logger.error(f"Error getting childs of {parent_id}", exc_info=True)
            return None

    def get_child_attack_patterns_recursive(self, parent_id) -> list:
        childs = self.get_child_attack_patterns_by_id(parent_id)
        if childs is None or len(childs) == 0:
            return []
        else:
            for child in childs:
                childs = childs + self.get_child_attack_patterns_recursive(child)
            return childs

    def get_child_attack_patterns(self, parent_ids, show_tree=False):
        if type(parent_ids) is not list: parent_ids = [parent_ids]
        childs = [parent_id for parent_id in parent_ids]
        if show_tree:
            childs = childs + [child for parent_id in parent_ids for child in self.get_child_attack_patterns_recursive(parent_id)]
        childs = list(set(childs))
        return childs # return only the ids, not the dataframe
    
class APIUtils:

    def allowed_file(self, filename, allowed_extensions):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions