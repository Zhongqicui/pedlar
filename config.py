"""pedlarweb configuration parameters."""
DEBUG = True # Turns on debugging for Flask
VERSION = "0.0.6" # Version of pedlar
SECRET_KEY = "secretmaster3000" # Secret key for sessions

BCRYPT_LOG_ROUNDS = 12 # Number of encryption rounds

SQLALCHEMY_DATABASE_URI = "sqlite://" # In memory database by default
SQLALCHEMY_TRACK_MODIFICATIONS = False # Disable event system

BROKER_URL = "tcp://localhost:7100" # Broker tcp endpoint
BROKER_TIMEOUT = 4000 # Milliseconds to wait for response
BROKER_LINGER = 2000 # Milliseconds to wait for closing broker socket
TICKER_URL = "tcp://localhost:7000" # Ticker tcp endpoint

GOOGLE_ANALYTICS = "" # GA Code UA-###
LEADERBOARD_SIZE = 10 # Displays top N users
RECENT_ORDERS_SIZE = 30 # Displays N most recent orders
TICK_HIST_SIZE = 40 # Number ticks in tick chart
