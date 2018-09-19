"""mt5 zmq test client."""
import argparse
import struct
import zmq

# pylint: disable=no-member

# Arguments
parser = argparse.ArgumentParser(description="Dummy agent for testing.")
parser.add_argument("--host", default="localhost", help="Server host.")
parser.add_argument("--port", default=7777, type=int, help="Server port.")
ARGS = parser.parse_args()

# Dump some info
print("libzmq:", zmq.zmq_version())
print("pyzmq:", zmq.pyzmq_version())

# Create context and socket
context = zmq.Context()
socket = context.socket(zmq.SUB)

# Set topic filter, this is a binary prefix
# to check for each incoming message
# set from server as uchar topic = X
socket.setsockopt(zmq.SUBSCRIBE, bytes.fromhex('00'))

addr = "tcp://" + ARGS.host + ':' + str(ARGS.port)
print("Connecting to server:", addr)
socket.connect(addr)

for _ in range(50):
  # unpack bytes https://docs.python.org/3/library/struct.html
  # we send uchar, double, double
  bid, ask = struct.unpack_from('dd', socket.recv(), 1) # offset topic
  print("BID:", bid, "ASK:", ask)
