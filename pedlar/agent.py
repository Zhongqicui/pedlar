"""mt5 zmq test client."""
import argparse
import logging
import struct
import zmq

logger = logging.getLogger(__name__)
logger.info("libzmq: %s", zmq.zmq_version())
logger.info("pyzmq: %s", zmq.pyzmq_version())

# pylint: disable=no-member

# Context are thread safe already,
# we'll create one global one for all agents
context = zmq.Context()


class Agent:
  """Base class for Pedlar trading agent."""
  name = "agent"

  def __init__(self, username="nobody", password="",
               ticker="tcp://localhost:7000",
               endpoint="http://localhost:8000"):
    self.username = username
    self.password = password
    self.ticker = ticker
    self.socket = None
    self.endpoint = endpoint
    self.isconnected = False

  @classmethod
  def from_args(cls, parents=None):
    """Create agent instance from command line arguments."""
    parser = argparse.ArgumentParser(description="Pedlar trading agent.", parents=parents or list())
    parser.add_argument("-u", "--username", default="nobody", help="Pedlar Web username.")
    parser.add_argument("-p", "--password", default="", help="Pedlar Web password.")
    parser.add_argument("-t", "--ticker", default="tcp://localhost:7000", help="Ticker endpoint.")
    parser.add_argument("-e", "--endpoint", default="tcp://localhost:7000", help="Pedlar Web endpoint.")
    return cls(**vars(parser.parse_args()))

  def connect(self):
    """Attempt to connect ticker and pedlarweb endpoints."""
    self.socket = context.socket(zmq.SUB)
    # Set topic filter, this is a binary prefix
    # to check for each incoming message
    # set from server as uchar topic = X
    # We'll subsribe to everything for now
    self.socket.setsockopt(zmq.SUBSCRIBE, bytes())
    # socket.setsockopt(zmq.SUBSCRIBE, bytes.fromhex('00'))
    logger.info("Connecting to ticker: %s", self.ticker)
    self.socket.connect(self.ticker)
    self.isconnected = True

  def on_tick(self, bid, ask):
    """On tick handler."""
    pass

  def on_bar(self, bopen, bhigh, blow, bclose):
    """On bar handler."""
    pass

  def run(self):
    """Start main loop and receive updates."""
    # Check connection
    if not self.isconnected:
      self.connect()
    # We'll trade forever until interrupted
    logger.info("Starting main trading loop...")
    try:
      while True:
        raw = self.socket.recv() # recv will BLOCK
        # unpack bytes https://docs.python.org/3/library/struct.html
        if len(raw) == 17:
          # We have tick data
          bid, ask = struct.unpack_from('dd', raw, 1) # offset topic
          self.on_tick(bid, ask)
        elif len(raw) == 33:
          # We have bar data
          bo, bh, bl, bc = struct.unpack_from('dddd', raw, 1) # offset topic
          self.on_bar(bo, bh, bl, bc)
    finally:
      logger.info("Stopping agent...")
