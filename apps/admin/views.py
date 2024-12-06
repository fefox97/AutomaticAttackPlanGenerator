
from flask import redirect, request, url_for
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user
from sqlalchemy import inspect


class MyModelView(ModelView):
    
    column_display_pk = True # optional, but I like to see the IDs in the list
    column_hide_backrefs = False
    column_display_all_relations = True

    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin

    def _handle_view(self, name, **kwargs):
        if not self.is_accessible():
            return redirect(url_for('authentication_blueprint.login', next=request.url))
        return None
    
class ToolCatalogueView(MyModelView):
    column_exclude_list = ['PostCondition', 'PreCondition', 'PreC', 'PreI', 'PreA', 'PostC', 'PostI', 'PostA']