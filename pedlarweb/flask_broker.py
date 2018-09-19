"""Broker extension for Flask."""
import logging
import struct
from flask import current_app, _app_ctx_stack

import zmq

logger = logging.getLogger(__name__)
# Context are thread safe already,
# we'll create one global one for all sockets
context = zmq.Context()

class Broker:
  """Handle ZMQ connection to broker."""
  def __init__(self, app=None):
    self.app = app
    self.context = zmq
    if app is not None:
      self.init_app(app)

  def init_app(self, app):
    """Initialise extension."""
    app.config.setdefault('BROKER_URL', "tcp://localhost:7100")
    app.config.setdefault('BROKER_POLLTIMEOUT', 500) # milliseconds
    app.teardown_appcontext(self.teardown)

  def connect(self):
    """Connect to broker server."""
    socket = context.socket(zmq.REQ)
    logger.info("Connecting to broker: %s", current_app.config['BROKER_URL'])
    socket.connect(current_app.config['BROKER_URL'])
    return socket

  @property
  def connection(self):
    """Broker connection socket."""
    ctx = _app_ctx_stack.top
    if ctx is not None:
      if not hasattr(ctx, 'broker'):
        socket = self.connect()
        poller = zmq.Poller()
        poller.register(socket, zmq.POLLIN)
        ctx.broker = (socket, poller)
      return ctx.broker

  def teardown(self, _):
    """Clean up socket."""
    ctx = _app_ctx_stack.top
    if hasattr(ctx, 'broker'):
      ctx.broker[0].close()

  def talk(self, order_id=0, volume=0.01, action=0):
    """Round of request-response with broker."""
    # Prepare request, ulong order_id, double volume, uchar action
    req = struct.pack('LdB', order_id, volume, action)
    s, p = self.connection
    s.send(req)
    # Check response
    socks = p.poll(current_app.config['BROKER_POLLTIMEOUT'])
    if not socks:
      raise IOError("Broker timeout on response.")
    resp = socks[0][0].recv()
    # ulong order_id, double price
    return struct.unpack('Ld', resp)

  def buy(self, volume=0.01):
    """Place a long position."""
    try:
      order_id, price = self.talk(volume=volume, action=2)
      return {'order_id': order_id, 'price': price}
    except Exception as e:
      return {'error': str(e)}

  def sell(self, volume=0.01):
    """Place a short position."""
    pass
