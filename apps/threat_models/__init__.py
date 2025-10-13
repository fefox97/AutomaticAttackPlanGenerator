

from flask import Blueprint

blueprint = Blueprint(
    'threat_models_blueprint',
    __name__,
    url_prefix='/threat_models',
)
