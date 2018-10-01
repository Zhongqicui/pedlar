"""pedlarweb entry point."""
from flask import Flask

# pylint: disable=wrong-import-position

app = Flask(__name__, instance_relative_config=True)

# Load configuration
app.config.from_object('config')
app.config.from_pyfile('config.py')

# Load extensions here for now
from flask_bcrypt import Bcrypt
bcrypt = Bcrypt(app)

from flask_login import LoginManager
login_manager = LoginManager(app)
login_manager.login_view = "login"

from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy(app)

from flask_socketio import SocketIO
socketio = SocketIO(app)

from .flask_broker import Broker
broker = Broker(app)

from .flask_ticker import Ticker
ticker = Ticker(app, socketio)

# Load view endpoints
from . import views
