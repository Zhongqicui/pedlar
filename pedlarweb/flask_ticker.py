"""Ticker extension for Flask."""
import struct
from flask import current_app

from eventlet import spawn_n
from eventlet.green import zmq

# Context are thread safe already,
# we'll create one global one for all sockets
context = zmq.Context()

class Ticker:
  """Handle ZMQ connection to broker."""
  def __init__(self, app=None, socketio=None):
    self.app = app
    self.socketio = socketio
    if app is not None:
      self.init_app(app)
    spawn_n(self.run) # spawns eventlet co-routine

  @staticmethod
  def init_app(app):
    """Initialise extension."""
    app.config.setdefault('TICKER_URL', "tcp://localhost:7000")
    # We want the connection live forever
    # app.teardown_appcontext(self.teardown)

  def run(self):
    """Connect to ticker server and emit updates."""
    socket = context.socket(zmq.SUB)
    # Set topic filter, this is a binary prefix
    # to check for each incoming message
    # set from server as uchar topic = X
    # We'll subsribe to only tick updates for now
    socket.setsockopt(zmq.SUBSCRIBE, bytes.fromhex('00'))
    with self.app.app_context():
      current_app.logger.debug("Connecting to ticker: %s", current_app.config['TICKER_URL'])
      socket.connect(current_app.config['TICKER_URL'])
      while True:
        raw = socket.recv()
        # unpack bytes https://docs.python.org/3/library/struct.html
        bid, ask = struct.unpack_from('dd', raw, 1) # offset topic
        self.socketio.emit('tick', {'bid': round(bid, 5), 'ask': round(ask, 5)})
    # socket will be cleaned up at garbarge collection
