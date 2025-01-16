# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import Email, DataRequired, EqualTo, Length

# login and registration


class LoginForm(FlaskForm):
    username = StringField('Username',
                            id='username_login',
                            validators=[DataRequired()])
    password = PasswordField('Password',
                                id='pwd_login',
                                validators=[DataRequired()])


class CreateAccountForm(FlaskForm):
    username = StringField('Username',
                            id='username_create',
                            validators=[DataRequired()])
    email = StringField('Email',
                        id='email_create',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password',
                                id='pwd_create',
                                validators=[DataRequired()])

class GithubForm(FlaskForm):
    email = StringField('Email',
                        id='email_create',
                        validators=[DataRequired(), Email()])
    
class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email',
                        id='email_pass_reset',
                        validators=[DataRequired(), Email()])
    
class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', id='pwd_reset', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', id='pwd_reset_confirm', validators=[DataRequired(), EqualTo('password', message='Passwords must match'), Length(min=8, message='Password must be at least 8 characters long')])
