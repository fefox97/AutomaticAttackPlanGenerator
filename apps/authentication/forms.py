

from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import Email, DataRequired

# login and registration
class GithubForm(FlaskForm):
    email = StringField('Email',
                        id='email_create',
                        validators=[DataRequired(), Email()])
    