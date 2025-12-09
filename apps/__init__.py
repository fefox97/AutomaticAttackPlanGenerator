import os
import re
import sys

from celery import Celery
from flask import Flask, request
from flask_admin import Admin
from flask_sqlalchemy import SQLAlchemy
from importlib import import_module
from flask_assets import Environment, Bundle
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_mailman import Mail
from flask_security import Security, SQLAlchemyUserDatastore, user_registered
from flask import render_template as real_render_template
from apps.celery_module.celery_utils import make_celery

from flask_flatpages import FlatPages
from flask_socketio import SocketIO

db = SQLAlchemy()
security = Security()
myAdmin = Admin()
mail = Mail()
user_datastore = None
celery = Celery()
pages = FlatPages()
socketio = SocketIO()

def render_template(*args, **kwargs):
    tree = {}
    for page in pages:
        folder = getattr(page, 'folder', None)
        node = tree
        if folder:
            parts = folder.strip('/').split('/')
            for part in parts:
                node = node.setdefault(part, {})
            node.setdefault('__pages__', []).append(page)
        else:
            tree.setdefault('__pages__', []).append(page)
    return real_render_template(*args, **kwargs, pages=pages, wiki_tree=tree)

def register_extensions(app, user_datastore):
    db.init_app(app)
    security.init_app(app, datastore=user_datastore)
    myAdmin.init_app(app)
    mail.init_app(app)
    pages.init_app(app)

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
    for module_name in ('authentication', 'home', 'api', 'profile', 'risk_analysis', 'catalogs', 'penetration_tests', 'threat_models', 'errors', 'wiki', 'macm'):
        module = import_module('apps.{}.routes'.format(module_name))
        app.register_blueprint(module.blueprint)
    app.register_blueprint(github_blueprint, url_prefix="/login")

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
    
    @app.context_processor
    def inject_template_scope():
        injections = dict()

        def cookies_check():
            value = request.cookies.get('cookie_consent')
            return value == 'true'
        injections.update(cookies_check=cookies_check)

        return injections

from apps.authentication.models import Roles, Users, Tasks
from apps.databases.models import App, Bibliography, Macm, Capec, MacmChecks, MacmUser, Attack, Protocols, Settings, ToolCatalogue, MethodologyCatalogue, ThreatCatalogue, PentestPhases, AssetTypes
from apps.admin.views import MyAdminIndexView, MyModelView, ThreatCatalogueView
from flask_admin.menu import MenuLink

def configure_admin(app):
    myAdmin.base_template = 'admin/index.html'
    myAdmin._set_admin_index_view(MyAdminIndexView(url='/', endpoint='admin'))
    myAdmin.add_link(MenuLink(name='Back Home', url='/'))
    myAdmin.add_view(MyModelView(Users, db.session, name='Users', category='Users'))
    myAdmin.add_view(MyModelView(Roles, db.session, name='Roles', category='Users'))
    myAdmin.add_view(MyModelView(Tasks, db.session, name='Tasks', category='Users'))
    myAdmin.add_view(MyModelView(App, db.session, name='App', category='App'))
    myAdmin.add_view(MyModelView(Macm, db.session, name='MACM', category='App'))
    myAdmin.add_view(MyModelView(Capec, db.session, name='CAPEC', category='Catalogs'))
    myAdmin.add_view(MyModelView(MacmUser, db.session, name='MACM User', category='App'))
    myAdmin.add_view(MyModelView(Attack, db.session, name='Attack', category='App'))
    myAdmin.add_view(MyModelView(ToolCatalogue, db.session, name='Tool Catalogue', category='Catalogs'))
    myAdmin.add_view(MyModelView(MethodologyCatalogue, db.session, name='Methodology Catalogue', category='Catalogs'))
    myAdmin.add_view(MyModelView(AssetTypes, db.session, name='Asset Types', category='Catalogs'))
    myAdmin.add_view(MyModelView(Protocols, db.session, name='Protocols', category='Catalogs'))
    myAdmin.add_view(ThreatCatalogueView(ThreatCatalogue, db.session, name='Threat Catalogue', category='Catalogs'))
    myAdmin.add_view(MyModelView(PentestPhases, db.session, name='Pentest Phases', category='Catalogs'))
    myAdmin.add_view(MyModelView(Settings, db.session, name='Settings'))
    myAdmin.add_view(MyModelView(Bibliography, db.session, name='Bibliography'))
    myAdmin.add_view(MyModelView(MacmChecks, db.session, name='MACM Checks', category='App'))

def clean_tasks(app):
    @app.before_request
    def clean_tasks():
        tasks = Tasks.query.all()
        for task in tasks:
            db.session.delete(task)
        db.session.commit()

def configure_roles(app):
    @app.before_request
    def create_roles():
        app.user_datastore.find_or_create_role(name='admin', description='Administrator')
        app.user_datastore.find_or_create_role(name='end-user', description='User')
        app.user_datastore.find_or_create_role(name='editor', description='Editor')
        app.user_datastore.find_or_create_role(name='api-user', description='API User')
        db.session.commit()
        user_registered.connect_via(app)(user_registered_sighandler)
    
    from apps.authentication.util import notify_admins
    def user_registered_sighandler(app, user, **extra):
        default_role = app.user_datastore.find_role("end-user")
        app.user_datastore.add_role_to_user(user, default_role)
        app.user_datastore.commit()
        notify_admins(user)

def initialize_database(app):
    try:
        db.create_all()
    except Exception as e:

        print('> Error: DBMS Exception: ' + str(e) )

        # fallback to SQLite
        basedir = os.path.abspath(os.path.dirname(__file__))
        app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'db.sqlite3')

        print('> Fallback to SQLite ')
        db.create_all()

def configure_database(app):
    @app.teardown_request
    def shutdown_session(exception=None):
        db.session.remove()

from apps.authentication.oauth import github_blueprint
from apps.notifications import notify

def create_app(config):
    app = Flask(__name__)
    app.config.from_object(config)

    user_datastore = SQLAlchemyUserDatastore(db, Users, Roles)
    app.user_datastore = user_datastore

    register_extensions(app, user_datastore)
    register_blueprints(app)
    register_assets(app)
    register_custom_filters(app)

    with app.app_context():
        initialize_database(app)
    configure_database(app)
    configure_admin(app)
    configure_roles(app)

    celery = make_celery(app)
    celery.conf.update(app.config, namespace='CELERY')
    app.extensions['celery'] = celery

    socketio.init_app(app, cors_allowed_origins="*", async_mode='eventlet', message_queue=app.config['REDIS_URL'])
    app.extensions['socketio'] = socketio

    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=2)

    clear_tmp(app.config['TMP_FOLDER'])
    # clean_tasks(app)
    return app

class MyDict(dict):
    def __missing__(self, key):
        return key.join("{}")