# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

import os
from   sys import exit

from flask import Flask

from apps.celery_module.celery_utils import make_celery
from apps.config import config_dict

DEBUG = (os.getenv('DEBUG', 'False') == 'True')
get_config_mode = 'Debug' if DEBUG else 'Production'

try:
    app_config = config_dict[get_config_mode.capitalize()]
except KeyError:
    exit('Error: Invalid <config_mode>. Expected values [Debug, Production] ')

app = Flask(__name__)
app.config.from_object(app_config)
celery = make_celery(app)
celery.conf.update(app.config)
app.app_context().push()