# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

import os
import re

from flask import Flask
from flask_admin import Admin
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from importlib import import_module
from flask_modals import Modal
from flask_assets import Environment, Bundle

db = SQLAlchemy()
login_manager = LoginManager()
modal = Modal()
myAdmin = Admin()

def register_extensions(app):
    db.init_app(app)
    login_manager.init_app(app)
    modal.init_app(app)
    myAdmin.init_app(app)

def clear_tmp(path):
    for root, dirs, files in os.walk(path):
        for file in files:
            os.remove(os.path.join(root, file))

def register_assets(app):
    assets = Environment(app)
    assets.debug = app.debug
    app.config['ASSETS_DEBUG'] = True
    assets.url = app.static_url_path
    scss = Bundle('assets/scss/volt.scss', filters='libsass', output='assets/css/volt-scss.css', depends='assets/scss/**/*.scss')
    bundles = {
        'css_all': scss
    }
    assets.register(bundles)
    scss.build()

def register_blueprints(app):
    for module_name in ('authentication', 'home', 'api'):
        module = import_module('apps.{}.routes'.format(module_name))
        app.register_blueprint(module.blueprint)

def register_error_handlers(app):
    module = import_module('apps.errors.routes')
    app.register_error_handler(404, module.page_not_found)
    app.register_error_handler(500, module.internal_server_error)

def register_custom_filters(app):
    @app.template_filter('regex_replace')
    def regex_replace(s, find, replace):
        return re.sub(find, replace, s)
    
    @app.template_filter('regex_split')
    def regex_split(s, find):
        return re.split(find, s)
    
    @app.template_filter('safe_substitute')
    def safe_substitute(s, in_dict):
        if type(in_dict) is not dict:
            in_dict = {}
        out_dict = MyDict(in_dict)
        return s.format_map(out_dict)

from apps.authentication.models import Users
from apps.databases.models import Macm
from apps.admin.views import MyModelView
from flask_admin.contrib.sqla import ModelView

def configure_admin(app):
    myAdmin.url = '/admin'
    myAdmin.base_template = 'admin/index.html'
    myAdmin.add_view(ModelView(Users, db.session, name='Users'))
    myAdmin.add_view(ModelView(Macm, db.session, name='MACM'))


def configure_database(app):

    @app.before_first_request
    def initialize_database():
        try:
            db.create_all()
        except Exception as e:

            print('> Error: DBMS Exception: ' + str(e) )

            # fallback to SQLite
            basedir = os.path.abspath(os.path.dirname(__file__))
            app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'db.sqlite3')

            print('> Fallback to SQLite ')
            db.create_all()

    @app.teardown_request
    def shutdown_session(exception=None):
        db.session.remove()

from apps.authentication.oauth import github_blueprint

def create_app(config):
    app = Flask(__name__)
    app.config.from_object(config)
    register_extensions(app)
    register_blueprints(app)
    register_error_handlers(app)
    register_assets(app)
    register_custom_filters(app)

    app.register_blueprint(github_blueprint, url_prefix="/login") 
    
    configure_database(app)
    # configure_admin(app)
    
    clear_tmp(app.config['TMP_FOLDER'])
    return app

class MyDict(dict):
    def __missing__(self, key):
        return key.join("{}")