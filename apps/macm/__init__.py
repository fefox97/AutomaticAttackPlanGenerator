

from flask import Blueprint

blueprint = Blueprint(
    'macm_blueprint',
    __name__,
    url_prefix='/macm'
)
