# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask import Blueprint
from .utils import AttackPatternUtils

blueprint = Blueprint(
    'api_blueprint',
    __name__,
    url_prefix='/api'
)

attack_pattern_utils = AttackPatternUtils()