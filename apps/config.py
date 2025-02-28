

import os, random, string
from dotenv import load_dotenv

class Config(object):

    basedir = os.path.abspath(os.path.dirname(__file__))

    # Load .env file
    load_dotenv()

    # Flask Security
    USERS_ROLES  = {
        'USER': {
            'name': 'User',
            'permissions': { 'user-read', 'user-write' }
        },
        'ADMIN': {
            'name': 'Admin',
            'permissions': { 'admin-read', 'admin-write' }
        },
    }

    PROPAGATE_EXCEPTIONS = False

    SECURITY_PASSWORD_SALT = os.getenv("SECURITY_PASSWORD_SALT", '146585145368132386173505678016728509634')
    SECURITY_EMAIL_VALIDATOR_ARGS = {"check_deliverability": False}
    SECURITY_REGISTERABLE = os.getenv('SECURITY_REGISTERABLE', True)
    SECURITY_CONFIRMABLE = os.getenv('SECURITY_CONFIRMABLE', True)
    SECURITY_RECOVERABLE = os.getenv('SECURITY_RECOVERABLE', True)
    SECURITY_CHANGEABLE = os.getenv('SECURITY_CHANGEABLE', True)
    SECURITY_SEND_REGISTER_EMAIL = os.getenv('SECURITY_SEND_REGISTER_EMAIL', True)
    SECURITY_DEFAULT_REMEMBER_ME = os.getenv('SECURITY_DEFAULT_REMEMBER_ME', True)
    SECURITY_POST_LOGIN_VIEW = os.getenv('SECURITY_POST_LOGIN_VIEW', 'index')
    SECURITY_POST_REGISTER_VIEW = os.getenv('SECURITY_POST_REGISTER_VIEW', 'login')
    SECURITY_POST_LOGOUT_VIEW = os.getenv('SECURITY_POST_LOGOUT_VIEW', 'login')
    SECURITY_USERNAME_ENABLE = os.getenv('SECURITY_USERNAME_ENABLE', True)
    SECURITY_USERNAME_REQUIRED = os.getenv('SECURITY_USERNAME_REQUIRED', True)
    SECURITY_TRACKABLE = os.getenv('SECURITY_TRACKABLE', True)
    SECURITY_CHANGE_EMAIL = os.getenv('SECURITY_CHANGE_EMAIL', True)
    SECURITY_POST_CHANGE_VIEW = os.getenv('SECURITY_POST_CHANGE_VIEW', 'change')

    # Site info
    URL = os.getenv('URL', 'https://localhost')
    SITE_NAME = os.getenv('SITE_NAME', 'VSecLab')

    # OpenRouter Management
    OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', None)

    # Celery
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
    
    # Assets Management
    ASSETS_ROOT = os.getenv('ASSETS_ROOT', '/static/assets')
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', f'{basedir}/static/uploads')
    TMP_FOLDER = os.getenv('TMP_FOLDER', f'{basedir}/static/.tmp')
    ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])
    
    # Set up the App SECRET_KEY
    SECRET_KEY  = os.getenv('SECRET_KEY', None)
    if not SECRET_KEY:
        SECRET_KEY = ''.join(random.choice( string.ascii_lowercase  ) for i in range( 32 ))

    # Set up the Mail Server
    MAIL_SERVER   = os.getenv('MAIL_SERVER', None)
    MAIL_PORT     = os.getenv('MAIL_PORT', None)
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', None)
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', None)
    MAIL_USE_TLS  = os.getenv('MAIL_USE_TLS', None)
    MAIL_USE_SSL  = os.getenv('MAIL_USE_SSL', None)
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', None)
    MAIL_BACKEND = os.getenv('MAIL_BACKEND', None)
    RESET_PASSWORD_LIMIT = os.getenv('RESET_PASSWORD_LIMIT', 350)

    # Set up the App JIRA
    JIRA_URL  = os.getenv('JIRA_URL', None)
    JIRA_PROJECT  = os.getenv('JIRA_PROJECT', None)
    JIRA_TICKET_TYPE  = os.getenv('JIRA_TICKET_TYPE', None)
    JIRA_USERNAME  = os.getenv('JIRA_USERNAME', None)
    JIRA_API_KEY  = os.getenv('JIRA_API_KEY', None)

    # Social AUTH context
    SOCIAL_AUTH_GITHUB  = False

    GITHUB_CLIENT_ID      = os.getenv('GITHUB_ID'    , None)
    GITHUB_CLIENT_SECRET  = os.getenv('GITHUB_SECRET', None)

    # Enable/Disable Github Social Login    
    if GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET:
        SOCIAL_AUTH_GITHUB  = True        

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    DB_ENGINE   = os.getenv('DB_ENGINE'   , None)
    DB_USERNAME = os.getenv('DB_USERNAME' , None)
    DB_PASS     = os.getenv('DB_PASS'     , None)
    DB_HOST     = os.getenv('DB_HOST'     , None)
    DB_PORT     = os.getenv('DB_PORT'     , None)
    DB_NAME     = os.getenv('DB_NAME'     , None)

    DATABASE_URL = os.getenv('DATABASE_URL', None)

    USE_SQLITE  = True

    DBS_PATH                    = os.getenv('DBS_PATH'    , None)
    THREAT_CATALOG_FILE_NAME    = os.getenv('THREAT_CATALOG_FILE_NAME'    , None)
    URI_NEO4J                   = os.getenv('URI_NEO4J'    , None)
    URI_NEO4J_WSS               = os.getenv('URI_NEO4J_WSS'    , None)
    USER_NEO4J                  = os.getenv('USER_NEO4J'    , None)
    PASS_NEO4J                  = os.getenv('PASS_NEO4J'    , None)
    TLS_NEO4J                   = os.getenv('TLS_NEO4J'    , None)

    # try to set up a Relational DBMS
    # if DB_ENGINE and DB_NAME and DB_USERNAME:

    #     try:
            
    #         # Relational DBMS: PSQL, MySql
    #         SQLALCHEMY_DATABASE_URI = '{}://{}:{}@{}:{}/{}'.format(
    #             DB_ENGINE,
    #             DB_USERNAME,
    #             DB_PASS,
    #             DB_HOST,
    #             DB_PORT,
    #             DB_NAME
    #         ) 

    #         USE_SQLITE  = False

    #     except Exception as e:

    #         print('> Error: DBMS Exception: ' + str(e) )
    #         print('> Fallback to SQLite ')    

    if DATABASE_URL not in [None, '']:
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
        USE_SQLITE = False

    if USE_SQLITE:

        # This will create a file in <app> FOLDER
        SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'db.sqlite3')
    
class ProductionConfig(Config):
    DEBUG = False

    # Security
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = 3600

class DebugConfig(Config):
    DEBUG = True

# Load all possible configurations
config_dict = {
    'Production': ProductionConfig,
    'Debug'     : DebugConfig
}
