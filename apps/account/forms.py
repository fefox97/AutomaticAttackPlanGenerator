# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import Email, DataRequired, EqualTo, Length

# login and registration


class DeleteAccountForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])