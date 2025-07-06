from apps.wiki import blueprint
from apps import pages, render_template
from flask import current_app as app, request

@blueprint.route('/')
def wiki_index():
    return render_template('wiki/index.html', segment='index')

@blueprint.route('/<path:path>', methods=['GET'])
def wiki_page(path):
    app.logger.info('Wiki page requested: {}'.format(path))
    page = pages.get_or_404(path)
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



