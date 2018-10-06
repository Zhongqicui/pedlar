"""Web forms for pedlarweb."""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Regexp, Length


class UserPasswordForm(FlaskForm):
  """Username password form used for login."""
  # \w is [0-9a-zA-Z_]
  username = StringField('User or Team name',
                         validators=[DataRequired(),
                                     Regexp(r"^\w(\w| )*\w$",
                                            message="At least 2 alphanumeric characters with only spaces in between.")
                                    ]
                         )
  password = PasswordField('Password', validators=[DataRequired(), Length(min=4)])
