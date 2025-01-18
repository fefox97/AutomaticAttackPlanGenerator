from apps.errors import blueprint
from flask import render_template, request
from flask import current_app as app

# handle if template is not found
@blueprint.errorhandler(404)
def page_not_found(e):
    app.logger.error('Exception occurred while trying to serve ' + request.path, exc_info=True)
    return render_template('errors/page-404.html'), 404

@blueprint.errorhandler(500)
def internal_server_error(e):
    return render_template('errors/page-500.html'), 500

@blueprint.errorhandler(403)
def access_forbidden(e):
    return render_template('errors/page-403.html'), 403