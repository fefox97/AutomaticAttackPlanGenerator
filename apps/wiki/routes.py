from apps.databases.models import AssetTypes
from apps.wiki import blueprint
from apps import pages, render_template
from flask import current_app as app, request
from apps.my_modules.utils import MacmUtils

@blueprint.route('/')
def wiki_index():
    return render_template('wiki/index.html', segment='index')

@blueprint.route('/macm_examples')
def macm_examples():
    macm_utils = MacmUtils()
    database = 'wordpress'
    neo4j_params = {
        "uri": app.config['URI_NEO4J_WSS'],
        "user": app.config['USER_NEO4J'],
        "password": app.config['PASS_NEO4J'],
        "encrypted": app.config['TLS_NEO4J']
    }
    asset_types_colors = AssetTypes.get_colors()
    if not macm_utils.check_database_exists(database):
        macm_utils.create_database(database)
        with open('apps/templates/wiki/macm_examples/Wordpress.macm', 'r') as file:
            macm_utils.make_query(file.read(), database)
    else:
        app.logger.info(f'Database {database} already exists, skipping creation.')
    return render_template('wiki/macm_examples/macm_examples.html', segment=get_segment(request), neo4j_params=neo4j_params, asset_types_colors=asset_types_colors)

@blueprint.route('/<path:path>', methods=['GET'])
def wiki_page(path):
    app.logger.info('Wiki page requested: {}'.format(path))
    page = pages.get_or_404(path)
    page.html = page.html.replace('src="./images/', 'src="/static/assets/wiki/images/')
    template = page.meta.get('template', 'wiki/flatpage.html')
    return render_template(template, page=page, segment=get_segment(request))


# Helper - Extract current page name from request
def get_segment(request):
    try:
        segment = request.path.split('/')
        if segment == '':
            segment = 'index'
        return segment
    except:
        return None



