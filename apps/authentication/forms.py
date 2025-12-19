from flask_wtf import FlaskForm
from wtforms import BooleanField, StringField
from wtforms.validators import DataRequired, Email, ValidationError
from flask_security.forms import ConfirmRegisterForm
import socket
from dns.resolver import resolve

class GithubForm(FlaskForm):
    email = StringField(
        'Email',
        id='email_create',
        validators=[DataRequired(), Email()],
    )


class ExtendedRegisterForm(ConfirmRegisterForm):
    email = StringField(
        'Email',
        validators=[
            DataRequired(message='Email is required.'),
            Email(message='Please enter a valid email address.'),
        ],
    )
    accept_terms = BooleanField(
        'terms',
        validators=[DataRequired(message='You must accept the terms and conditions.')],
    )

    def validate(self, extra_validators=None):
        if not super().validate():
            if 'Please review the information entered in the registration form.' not in self.form_errors:
                self.form_errors.append('Please review the information entered in the registration form.')
            return False
        return True

    def validate_email(self, field):
        address = (field.data or '').strip()
        if '@' not in address:
            return

        domain = address.rsplit('@', 1)[1]
        if not domain:
            return

        if resolve:
            try:
                resolve(domain, 'MX')
                return
            except Exception:
                if self._domain_has_address_record(domain):
                    return
                raise ValidationError('Email domain does not exist.')

        if not self._domain_has_address_record(domain):
            raise ValidationError('Email domain does not exist.')

    @staticmethod
    def _domain_has_address_record(domain):
        try:
            socket.getaddrinfo(domain, None)
        except socket.gaierror:
            return False
        return True