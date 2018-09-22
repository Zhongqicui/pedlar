"""Interactive agent."""
from .agent import Agent


class InteractiveAgent(Agent):
  """Basic trading agent."""
  name = "interactive"
  # Override run and ask for user input instead
  def run(self):
    """Execute user commands."""
    self.connect()
    try:
      while True:
        # Get user input and perform action
        a = input("[b]uy [s]ell [c]lose [q]uit: ")
        if a == 'b':
          self.buy()
        elif a == 's':
          self.sell()
        elif a == 'c':
          self.close()
        elif a == 'q':
          break
    finally:
      self.disconnect()

if __name__ == "__main__":
  import logging
  logging.basicConfig(level=logging.INFO)
  # Requests dumps a lot of logs, we will reduce its verbosity
  logging.getLogger('requests').setLevel(logging.ERROR)
  agent = InteractiveAgent.from_args()
  agent.run()
