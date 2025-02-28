

from itsdangerous import URLSafeTimedSerializer
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin
from flask import current_app as app

from apps import db
from flask_security import RoleMixin, UserMixin

class Users(db.Model, UserMixin):

    __tablename__ = 'Users'

    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(64), unique=True)
    email         = db.Column(db.String(64), unique=True)
    password      = db.Column(db.String(255))
    active        = db.Column(db.Boolean, default=True, nullable=False)
    created_on    = db.Column(db.DateTime, default=db.func.now())
    updated_on    = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())
    oauth_github  = db.Column(db.String(100), nullable=True)
    fs_uniquifier = db.Column(db.String(64), unique=True)
    confirmed_at  = db.Column(db.DateTime, nullable=True)
    current_login_at = db.Column(db.DateTime, nullable=True)
    last_login_at = db.Column(db.DateTime, nullable=True)
    current_login_ip = db.Column(db.String(100), nullable=True)
    login_count = db.Column(db.Integer, nullable=True)
    roles         = db.relationship('Roles', secondary='roles_users', backref=db.backref('users', lazy='dynamic'))

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            # depending on whether value is an iterable or not, we must
            # unpack it's value (when **kwargs is request.form, some values
            # will be a 1-element list)
            # if hasattr(value, '__iter__') and not isinstance(value, str):
            #     # the ,= unpack of a singleton fails PEP8 (travis flake8 test)
            #     value = value[0]
            # if isinstance(value, str):
            #     value = value.encode('utf-8')
            # if property == 'password':
            #     value = hash_pass(value)  # we need bytes here (not plain str)

            setattr(self, property, value)

    def __repr__(self):
        return str(self.username) 
    
    @staticmethod
    def validate_reset_password_token(token, user_id):
        user = Users.query.filter_by(id=user_id).first()
        if user is None:
            return None
        
        serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
        
        try:
            email = serializer.loads(
                token,
                salt=user.password,
                max_age=3600
            )
        except:
            return None

        if user.email != email:
            return None
        
        return user
    
# @login_manager.user_loader
# def user_loader(id):
#     return Users.query.filter_by(id=id).first()


# @login_manager.request_loader
# def request_loader(request):
#     username = request.form.get('username')
#     user = Users.query.filter_by(username=username).first()
#     return user if user else None

class OAuth(OAuthConsumerMixin, db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey("Users.id", ondelete="cascade"), nullable=False)
    user = db.relationship(Users)

class Roles(db.Model, RoleMixin):

    __tablename__ = 'Roles'

    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(255))

    def __repr__(self):
        return str(self.name)
    
class RolesUsers(db.Model):
    
    __tablename__ = 'roles_users'

    id      = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('Users.id', ondelete='CASCADE'))
    role_id = db.Column(db.Integer(), db.ForeignKey('Roles.id', ondelete='CASCADE'))

    def __repr__(self):
        return str(self.id)
    
class Tasks(db.Model):

    __tablename__ = 'Tasks'

    id            = db.Column(db.String(255), primary_key=True)
    name          = db.Column(db.String(255), nullable=False)
    app_id        = db.Column(db.String(100), db.ForeignKey('App.AppID', ondelete='CASCADE'))
    created_on    = db.Column(db.DateTime, default=db.func.now())
    updated_on    = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())
    user_id       = db.Column(db.Integer, db.ForeignKey('Users.id', ondelete='CASCADE'))
    user          = db.relationship(Users)

    def __repr__(self):
        return str(self.name)