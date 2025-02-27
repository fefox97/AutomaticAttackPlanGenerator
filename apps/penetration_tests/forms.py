from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import Email, DataRequired

# login and registration
class UploadMacmForm(FlaskForm):
    macmAppName = StringField('App Name',
                        id='macmAppName',
                        validators=[DataRequired()])