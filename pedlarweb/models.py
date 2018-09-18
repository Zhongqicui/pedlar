"""pedlarweb data models."""
from . import bcrypt, db, login_manager, app


class User(db.Model):
  """Single user instance."""
  id = db.Column(db.Integer, primary_key=True, autoincrement=True)
  username = db.Column(db.String(128), unique=True, nullable=False)
  _password = db.Column("password", db.String(128), nullable=False)

  @property
  def password(self):
    return self._password

  @password.setter
  def password(self, plaintext):
    self._password = bcrypt.generate_password_hash(plaintext)

  def is_correct_password(self, plaintext):
    return bcrypt.check_password_hash(self._password, plaintext)

  @property
  def is_active(self):
    return True

  @property
  def is_authenticated(self):
    return True

  @property
  def is_anonymous(self):
    return False

  def get_id(self):
    return str(self.id)

# Handle Flask-Login loading
@login_manager.user_loader
def load_user(user_id):
  return User.query.get(user_id)

# Check for in memory database
if app.config['SQLALCHEMY_DATABASE_URI'] == "sqlite://":
  db.create_all()
