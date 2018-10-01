"""Broker extension for Flask."""
import struct
from flask import current_app, _app_ctx_stack, abort

from eventlet.green import zmq

# Context are thread safe already,
# we'll create one global one for all sockets
context = zmq.Context()

class Broker:
  """Handle ZMQ connection to broker."""
  def __init__(self, app=None):
    self.app = app
    if app is not None:
      self.init_app(app)

  def init_app(self, app):
    """Initialise extension."""
    app.config.setdefault('BROKER_URL', "tcp://localhost:7100")
    app.config.setdefault('BROKER_TIMEOUT', 4000)
    app.config.setdefault('BROKER_LINGER', 2000)
    app.teardown_appcontext(self.teardown)

  @staticmethod
  def connect():
    """Connect to broker server."""
    socket = context.socket(zmq.REQ)
    socket.setsockopt(zmq.RCVTIMEO, current_app.config['BROKER_TIMEOUT'])
    socket.setsockopt(zmq.LINGER, current_app.config['BROKER_LINGER'])
    current_app.logger.debug("Connecting to broker: %s", current_app.config['BROKER_URL'])
    socket.connect(current_app.config['BROKER_URL'])
    return socket

  @property
  def connection(self):
    """Broker connection socket."""
    ctx = _app_ctx_stack.top
    if not hasattr(ctx, 'broker'):
      ctx.broker = self.connect()
    return ctx.broker

  @staticmethod
  def teardown(_):
    """Clean up socket."""
    ctx = _app_ctx_stack.top
    if hasattr(ctx, 'broker'):
      current_app.logger.debug("Disconnecting from broker: %s", current_app.config['BROKER_URL'])
      ctx.broker.close()

  @staticmethod
  def validate(req):
    """Validate given request.
    :return: true on successful validation false otherwise
    """
    cond = (req and req.get('order_id', 0) >= 0 and
            req.get('volume', 0.01) >= 0.01 and
            req.get('volume', 0.01) <= 1.0 and
            req.get('action', 0) in (0, 1, 2, 3))
    return cond

  def talk(self, order_id=0, volume=0.01, action=0):
    """Round of request-response with broker."""
    # Prepare request, ulong order_id, double volume, uchar action
    req = struct.pack('LdB', order_id, volume, action)
    sock = self.connection
    # Handled in a non-blocking fashion by eventlet
    sock.send(req)
    # Check response
    resp = sock.recv()
    # ulong order_id, double price, double profit, uint retcode
    order_id, price, profit, retcode = struct.unpack('LddI', resp)
    return {'order_id': order_id, 'price': price, 'profit': profit, 'retcode': retcode}

  def handle(self, request):
    """Handle a client request."""
    # Validate request first
    if not self.validate(request):
      abort(400)
    # Make the request to the broker
    resp = {'retcode': -1} # Assume failure
    try:
      resp = self.talk(**request)
    except zmq.Again:
      current_app.logger.error("Broker response timed out.")
      # abort(504) # Gateway Timeout
    # Check response conditions
    if resp['retcode'] != 0:
      current_app.logger.error("Broker returned a non-zero return code.")
      abort(503) # Service Unavailable
    if request['action'] in (2, 3) and resp['order_id'] == 0:
      # We asked for a trade but did not get an id
      current_app.logger.error("Broker did not place order.")
      abort(503)
    return resp
