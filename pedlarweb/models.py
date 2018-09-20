"""pedlarweb data models."""
import datetime
from . import bcrypt, db, login_manager, app


class User(db.Model):
  """Single user instance."""
  id = db.Column(db.Integer, primary_key=True, autoincrement=True)
  username = db.Column(db.String(128), unique=True, nullable=False)
  _password = db.Column("password", db.String(128), nullable=False)
  isadmin = db.Column(db.Boolean(), nullable=False, default=False)
  orders = db.relationship('Order', cascade='all,delete', backref='user', lazy=True)
  last_login = db.Column(db.DateTime(), nullable=False, default=datetime.datetime.now())
  joined = db.Column(db.DateTime(), nullable=False, default=datetime.datetime.now())

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


class Order(db.Model):
  """Single trade order."""
  id = db.Column(db.Integer, primary_key=True)
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
  type = db.Column(db.String(8), nullable=False)
  price_open = db.Column(db.Float(), nullable=False)
  price_close = db.Column(db.Float())
  profit = db.Column(db.Float())
  closed = db.Column(db.DateTime())
  created = db.Column(db.DateTime(), nullable=False, default=datetime.datetime.now())

# Check for in memory database
if app.config['SQLALCHEMY_DATABASE_URI'] == "sqlite://":
  db.create_all()
