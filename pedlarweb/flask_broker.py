"""Broker extension for Flask."""
import struct
from flask import current_app, _app_ctx_stack, abort

import zmq

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
    app.config.setdefault('BROKER_POLLTIMEOUT', 1000) # milliseconds
    app.teardown_appcontext(self.teardown)

  @staticmethod
  def connect():
    """Connect to broker server."""
    socket = context.socket(zmq.REQ)
    current_app.logger.debug("Connecting to broker: %s", current_app.config['BROKER_URL'])
    socket.connect(current_app.config['BROKER_URL'])
    return socket

  @property
  def connection(self):
    """Broker connection socket."""
    ctx = _app_ctx_stack.top
    if not hasattr(ctx, 'broker'):
      socket = self.connect()
      socket.set(zmq.LINGER, 2000)
      poller = zmq.Poller()
      poller.register(socket, zmq.POLLIN)
      ctx.broker = (socket, poller)
    return ctx.broker

  @staticmethod
  def teardown(_):
    """Clean up socket."""
    ctx = _app_ctx_stack.top
    if hasattr(ctx, 'broker'):
      current_app.logger.debug("Disconnecting from broker: %s", current_app.config['BROKER_URL'])
      ctx.broker[0].close()

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
    s, p = self.connection
    s.send(req)
    # Check response
    socks = p.poll(current_app.config['BROKER_POLLTIMEOUT'])
    if not socks:
      raise IOError("Broker timeout on response.")
    resp = socks[0][0].recv()
    # ulong order_id, double price, double profit, uint retcode
    order_id, price, profit, retcode = struct.unpack('LddI', resp)
    return {'order_id': order_id, 'price': price, 'profit': profit, 'retcode': retcode}

  def handle(self, request):
    """Handle a client request."""
    # Validate request first
    if not self.validate(request):
      abort(400)
    # Make the request to the broker
    try:
      resp = self.talk(**request)
    except IOError:
      current_app.logger.warn("Broker response timed out.")
      abort(504) # Gateway Timeout
    # Check response conditions
    if resp['retcode'] != 0:
      current_app.logger.warn("Broker returned a non-zero return code.")
      abort(500)
    if request['action'] in (2, 3) and resp['order_id'] == 0:
      # We asked for a trade but did not get an id
      current_app.logger.warn("Broker did not place order.")
      abort(500)
    return resp
