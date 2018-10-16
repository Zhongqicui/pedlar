"""Local execution broker for Flask Broker."""
import argparse
from collections import namedtuple
import struct
import logging
from eventlet import GreenPool
from eventlet.green import zmq

# Designed to run locally only
if __name__ != "__main__":
  raise RuntimeError("Can only run as stand-alone script.")

# Setup Arguments
logger = logging.getLogger(__name__)
parser = argparse.ArgumentParser(description=__doc__, fromfile_prefix_chars='@')
parser.add_argument("-t", "--ticker", default="tcp://127.0.0.1:7000", help="Ticker URL")
parser.add_argument("-b", "--broker_host", default="tcp://127.0.0.1:7100", help="Broker serve URL")
parser.add_argument("-i", "--order_id", default=1, type=int, help="Initial order id")
parser.add_argument("-l", "--leverage", default=100, type=int, help="Account leverage")
ARGS = parser.parse_args()

# Context are thread safe already,
# we'll create one global one for all sockets
context = zmq.Context()
Order = namedtuple('Order', ['id', 'price', 'volume', 'type'])

# Globals
BID, ASK = 0.0, 0.0
ORDERS = dict() # Orders indexed using order id

def handle_tick():
  """Listen to incoming tick updates."""
  socket = context.socket(zmq.SUB)
  # Set topic filter, this is a binary prefix
  # to check for each incoming message
  # set from server as uchar topic = X
  # We'll subsribe to only tick updates for now
  socket.setsockopt(zmq.SUBSCRIBE, bytes.fromhex('00'))
  logger.info("Connecting to ticker: %s", ARGS.ticker)
  socket.connect(ARGS.ticker)
  while True:
    raw = socket.recv()
    # unpack bytes https://docs.python.org/3/library/struct.html
    bid, ask = struct.unpack_from('dd', raw, 1) # offset topic
    logger.debug("Tick: %f %f", bid, ask)
    # We'll use global to pass tick data between green threads
    # since only 1 actually run at a time
    global BID, ASK # pylint: disable=global-statement
    BID, ASK = bid, ask
  # socket will be cleaned up at garbarge collection

def handle_broker():
  """Listen to incoming broker requests."""
  socket = context.socket(zmq.REP)
  socket.bind(ARGS.broker_host)
  logger.info("Broker listening on: %s", ARGS.broker_host)
  nextid = ARGS.order_id
  while True:
    raw = socket.recv()
    # Prepare request: ulong order_id, double volume, uchar action
    order_id, volume, action = struct.unpack('LdB', raw)
    # Prepare response: ulong order_id, double price, double profit, uint retcode
    resp = (order_id, 0.0, 0.0, 1) # Assume failure
    if action == 1 and order_id in ORDERS: # Close order
      # BIG ASSUMPTION, account currency is the same as base currency
      # Ex. GBP account trading on GBPUSD since we don't have other
      # exchange rates streaming to us to handle conversion
      order = ORDERS.pop(order_id)
      closep = BID if order.type == 2 else ASK
      diff = closep - order.price if order.type == 2 else order.price - closep
      profit = diff*ARGS.leverage*order.volume*1000*(1/closep)
      resp = (order_id, closep, round(profit, 2), 0)
      logger.info("CLOSING: %s", resp)
    elif action == 2 or action == 3: # Buy - Sell
      oprice = ASK if action == 2 else BID
      order = Order(id=nextid, price=oprice, volume=volume, type=action)
      ORDERS[nextid] = order
      logger.info("ORDER: %s", order)
      resp = (nextid, oprice, 0.0, 0)
      nextid += 1
    # Unknown action otherwise
    # Pack and send response
    resp = struct.pack('LddI', *resp)
    socket.send(resp)

# Spawn green threads
logging.basicConfig(level=logging.INFO)
pool = GreenPool()
try:
  pool.spawn_n(handle_tick)
  pool.spawn_n(handle_broker)
  pool.waitall() # Loops forever
finally:
  # There might some orphan orders left over
  print("ORPHANS:", ORDERS)
