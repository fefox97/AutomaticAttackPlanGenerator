# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask import Blueprint

blueprint = Blueprint(
    'penetration_tests_blueprint',
    __name__,
    url_prefix='/penetration_tests',
)
