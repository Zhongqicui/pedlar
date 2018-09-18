"""pedlarweb configuration parameters."""
DEBUG = True # Turns on debugging for Flask
SECRET_KEY = "secretmaster3000" # Secret key for sessions

BCRYPT_LOG_ROUNDS = 12 # Number of encryption rounds

SQLALCHEMY_DATABASE_URI = "sqlite://" # In memory database by default
SQLALCHEMY_TRACK_MODIFICATIONS = False # Disable event system
