# :chart_with_upwards_trend: pedlar
Pedlar is an algorithmic trading platform for Python designed for trading events, competitions and sessions such as Algothons. It includes a live web interface with multiple accounts with account sharing and live chat, an HTTP API with example Python trading agents and a [ZeroMQ](http://zeromq.org/) based broker connection to [MetaTrader5](https://www.metatrader5.com/en).

![pedlarweb](https://raw.githubusercontent.com/nuric/pedlar/master/pedlarweb_screenshot.jpg)

## Getting Started
If there is already a ticker server and web server running, the client API under `pedlar` can be used. If not, follow instructions on how to get them in the [Hosting](#hosting) section. The client or *agent* API resolves around connecting to the *ticker* server (where agents receive price updates) and the *web* server, in this case handles the broker connection. The ticker is separate to reduce overhead and latencies between making trades and just receiving price updates.

### Installation
The client API is can be installed using:

```bash
pip3 install --no-cache-dir -U pedlar
```

### Usage
There are some helpful examples in the `pedlar` folder. Here is a overview of the client API:

```python
from pedlar.agent import Agent

class MyAgent(Agent):
  """A trading agent."""
  def on_order(self, order):
    """Called on placing a new order."""
    print("New order:", order)
    print("Orders:", self.orders) # Agent orders only

  def on_order_close(self, order, profit):
    """Called on closing an order with some profit."""
    print("Order closed", order, profit)
    print("Current balance:", self.balance) # Agent balance only

  def on_tick(self, bid, ask):
    """Called on every tick update."""
    print("Tick:", bid, ask)
    # self.buy()
    # self.sell()
    # self.close()

  def on_bar(self, bopen, bhigh, blow, bclose):
    """Called on every bar update."""
    print("Bar:", bopen, bhigh, blow, bclose)

if __name__ == "__main__":
  import logging
  logging.basicConfig(level=logging.DEBUG)
  agent = MyAgent.from_args()
  agent.run()
```

The extra parameters are parsed from the command line and can be run using:

```bash
python3 -u myagent.py -h
```

Key things to keep in mind:

 - Every agent takes control of its own orders and balance, it is *not synced* across agents of a shared account. This setup is to keep agents isolated.
 - Agents try to close orders when they are quit, if hard stopped or an error occurs an open orphan order might remain. In this case, one option would be manually invoke `self.close` with the stale order id or simply reset the account.
 - The ticker connection receives from ZeroMQ whereas the trade requests are made via HTTP. There might some ticks dropped if the trade request takes too long.

### Basic Backtesting
The agents can backtest agaisnt a CSV file of the following format:

```
tick,1.29127,1.292
tick,1.29139,1.29212
tick,1.29145,1.29218
bar,1.29584,1.29606,1.29547,1.29554
tick,1.29138,1.29189
tick,1.29135,1.29186
tick,1.29134,1.29185
tick,1.29136,1.29187
tick,1.29133,1.29184
```

which can be used with an agent `python3 myagent.py -b ticks.csv`. Essentially each line will invoke corresponding `on_tick` or `on_bar` function. **The actual profit and trade results are computed offline based on absolute price differences.** This means the agent will run completely offline and the actual results are only useful to get an idea about the performance or train a neural network. Any broker commissions, price requotes etc are not factored.

## Hosting
Pedlar involves 4 components that talk to each other to create a platform for agents to trade:

 - **ticker:** is a ZeroMQ `PUB` socket that publishes tick and bar updates that are received by the agents which eventually trigger `on_tick` and `on_bar` methods. This component runs independently from others to provide a continuous stream of price updates.
 - **broker:** is the component that actually executes live order requests on the market. Pedlar is broker agnostic and all it needs is methods to buy, sell and close an order with unique order ids.
 - **pedlarweb**: is the main web server that handles user accounts, live leaderboard etc updates and agent trade requests.
 - **pedlar**: is the client API that allows for Python based clients to receive updates from *ticker* and make trade requests to *pedlarweb*.

### Repository Structure
The client and server packages are separated to avoid any assumptions between their implementations. The main folders include:

 - **mt5:** contains the MetaTrader 5 trading components that act as the *ticker* and the *broker* for live trading.
 - **pedlar:** contains the client API is the exposed API for building new agents.
 - **pedlarweb:** is the web server that bridges agent trade requests and broker while providing a web user interface and live updates.

### Prerequisites
All the extra packages required can be installed using:
```bash
pip3 install --no-cache-dir -U -r requirements.txt
```

### Running MT5
To get the ticker and broker components up and running you need to:

 1. [Install MetaTrader 5](https://www.metatrader5.com/en/download), or some existing installation would work.
 2. [Install ZeroMQ](http://zeromq.org/distro:microsoft-windows) for Windows since the scripts require the `libzmq.dll` to run. You might need to install a compatible [Visual C++](https://support.microsoft.com/en-gb/help/2977003/the-latest-supported-visual-c-downloads) runtime to get ZeroMQ running.
 3. Find the installed ZeroMQ `bin` folder and move the DLL to `Library\libzmq.dll` as that is where the `libzmq.mqh` header expects it.
 4. Copy files MetaTrader 5 files to the expected folders of your installation. An easy way to find that is to open the MetaEditor (F4 from trader) and right click on a folder to select *Open Folder*. For development it is easier to write a script that syncs the repo folder with the expected folders.
 5. Once the ticker and broker is compiled, you can attach them to any chart that you want the tick updates to be sent and trade orders to be handled. You can run multiple at different ports as well. From "Options" the "Allow DLL Imports" needs to be enabled for obvious reasons.
 6. If you get DLL import error, it is most likely because the ZeroMQ DLL isn't happy or the C++ runtime is not compatible.

### Running Web Server
The web server is a standard [Flask](http://flask.pocoo.org/) application organised into the `pedlarweb` package. Once the `config.py` options are as desired, a database can be initialised using:

```bash
python3 -c "from pedlarweb import db; db.create_all()"
```

If the in-memory default database is used, tables will be automatically created but *data is lost when server is stopped using an in-memory database.* Then the server can be run using standard Flask options:

```bash
export FLASK_APP=pedlarweb flask run
```

Due to [Flask-SocketIO](https://flask-socketio.readthedocs.io/en/latest/) the `eventlet` server would be run. For development the `FLASK_ENV=development` environment variable needs to be set. **For convinience, a new user is created if none with the username exist from the login page.** This choice is done to get people on-board as easy as possible without heavy registration and email confirmation schemes.

## FAQ

 - **Why ticker is separated from the web server?** This design choice is done to reduce overhead and latency in receiving price updates for agents. As a result agents need to connect to both the ticker and the web server to function unless backtesting.
 - **Why not use ZeroMQ for trade requests instead of HTTP?** HTTP APIs provide a more approachable and unified way of providing a service. HTTP does have more overhead but it makes it easier for other non-pedlar clients that talk to `pedlarweb` to be built as well. Finally, it has an authentication mechanism that is enforced for every request.
 - **Why is the source code 2 space indented?** The answer is a combination of personal style and to stop direct copy-paste from other resources. The code is linted using [PyLint](https://www.pylint.org/) although there are cases it is disabled on purpose.

## Limitations & To-Dos

 - Currently the API *supports trading only on a single instrument* mainly because the web server can talk to a single broker and a single broker can only be attached to single chart. The MT5 broker is fixed to the current chart `Symbol()` but there is space for passing the symbol, instrument from agent -> server -> broker. For the target audience of live sessions and competitions, a single instrument seems enough.
 - Although polling is employed for ZeroMQ sockets, they are still *blocking* in nature to avoid data loss. In that case, an agent can look like it has frozen against Ctrl+C. This case also occurs for MT5 ticker and broker scripts. The timeout on the polls can be adjust or a little patience helps.
 - There is a mixture of line endings due MT5 running on Windows and development is somewhat split between Windows and Linux environments. Hopefully, we live in a day and age this is not a problem anymore.

## Built With

 - [Flask](http://flask.pocoo.org/) - `pedlarweb` web framework
 - [ZeroMQ](http://zeromq.org/) - `ticker` and `broker` messaging framework
 - [MetaTrader5](https://www.metatrader5.com/en) - as the default trading platform
