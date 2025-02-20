

from flask import Blueprint

blueprint = Blueprint(
    'risk_analysis_blueprint',
    __name__,
    url_prefix='/risk_analysis'
)
