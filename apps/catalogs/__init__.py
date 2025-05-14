

from flask import Blueprint

blueprint = Blueprint(
    'catalogs_blueprint',
    __name__,
    url_prefix='/catalogs',
)
