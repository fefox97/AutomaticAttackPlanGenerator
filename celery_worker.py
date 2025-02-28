import os
from sys import exit

# from apps.celery_module.celery_utils import make_celery
from apps.config import config_dict
from run import app

DEBUG = (os.getenv('DEBUG', 'False') == 'True')
get_config_mode = 'Debug' if DEBUG else 'Production'

try:
    app_config = config_dict[get_config_mode.capitalize()]
except KeyError:
    exit('Error: Invalid <config_mode>. Expected values [Debug, Production] ')

celery = app.extensions['celery']
celery.conf.update(app.config)