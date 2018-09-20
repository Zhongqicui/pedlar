"""Basic agent."""
import argparse
from collections import deque

from .agent import Agent


class BasicAgent(Agent):
  """Basic trading agent."""
  name = "alice"
  def __init__(self, histsize=40, **kwargs):
    self.histsize = histsize
    self.past_ticks = deque(maxlen=histsize)
    self.period = 0
    self.past_avg = 0
    super().__init__(**kwargs) # Must call this

  def on_order(self, order):
    """On order handler."""
    print("ORDER:", order)

  def on_tick(self, bid, ask):
    """On tick handler."""
    print("TICK:", bid, ask)
    self.past_ticks.append(bid)
    # Fill the buffer
    if len(self.past_ticks) != self.histsize:
      return
    # Let's wait period many ticks
    if self.period < self.histsize:
      self.period += 1
      return
    # Compute average differences to see if price
    # going up or down and buy or sell
    avg = sum(self.past_ticks)/self.histsize
    if avg - self.past_avg > 0:
      self.buy()
    else:
      self.sell()
    self.past_avg = avg
    self.period = 0

  def on_bar(self, bopen, bhigh, blow, bclose):
    """On bar handler."""
    print("BAR:", bopen, bhigh, blow, bclose)

if __name__ == "__main__":
  import logging
  logging.basicConfig(level=logging.INFO)
  # Requests dumps a lot of logs, we will reduce its verbosity
  logging.getLogger('requests').setLevel(logging.ERROR)
  parser = argparse.ArgumentParser(add_help=False)
  parser.add_argument("--histsize", default=40, type=int, help="Agent tick history size.")
  agent = BasicAgent.from_args(parents=[parser])
  agent.run()
