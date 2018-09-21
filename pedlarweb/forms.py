"""Web forms for pedlarweb."""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Length


class UserPasswordForm(FlaskForm):
  """Username password form used for login."""
  username = StringField('User or Team name', validators=[DataRequired(), Length(min=4, max=128)])
  password = PasswordField('Password', validators=[DataRequired()])
