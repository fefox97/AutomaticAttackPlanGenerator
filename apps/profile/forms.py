

from flask_wtf import FlaskForm
from wtforms import PasswordField
from wtforms.validators import DataRequired

# login and registration


class DeleteAccountForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])