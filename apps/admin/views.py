
from flask import redirect, request
from flask_admin.contrib.sqla import ModelView
from flask_security import current_user, url_for_security


class MyModelView(ModelView):
    
    column_display_pk = True # optional, but I like to see the IDs in the list
    column_hide_backrefs = False
    column_display_all_relations = True

    def is_accessible(self):
        return current_user.is_authenticated and current_user.has_role('admin')

    def _handle_view(self, name, **kwargs):
        if not self.is_accessible():
            return redirect(url_for_security('login', next=request.url))
        return None
    
class ToolCatalogueView(MyModelView):
    column_exclude_list = ['PostCondition', 'PreCondition', 'PreC', 'PreI', 'PreA', 'PostC', 'PostI', 'PostA']