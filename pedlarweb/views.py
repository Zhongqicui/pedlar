"""Endpoints for the web application."""
import datetime

from flask import render_template, redirect, url_for, request, jsonify
from flask_login import login_user, login_required, current_user, logout_user
from flask_socketio import emit, join_room, leave_room

from . import app, db, broker, socketio
from .forms import UserPasswordForm
from .models import User, Order

@app.route('/login', methods=['GET', 'POST'])
def login():
  """Login user if not already logged in."""
  form = UserPasswordForm()
  if form.validate_on_submit():
    # For convenience we create users while they login
    user = User.query.filter_by(username=form.username.data).first()
    if user:
      if user.is_correct_password(form.password.data):
        login_user(user)
        user.last_login = datetime.datetime.now()
        db.session.commit()
        return redirect(url_for('index'))
      return redirect(url_for('login'))
    # Create new user
    user = User(username=form.username.data, password=form.password.data)
    db.session.add(user)
    db.session.commit()
    login_user(user)
    app.logger.info("New user: %s", user.username)
    return redirect(url_for('index'))
  return render_template('login.html', form=form)

def get_leaders():
  """Recompute return leaderboard."""
  leaders = [{'username': u.username, 'balance': u.balance}
             for u in User.query.order_by(User.balance.desc()).\
                      limit(app.config['LEADERBOARD_SIZE']).all()]
  return leaders

def rows_to_dicts(objs, attributes):
  """Convert SQLAlchemy object to dictionary."""
  l = list()
  for obj in objs:
    d = dict()
    for att in attributes:
      elem = getattr(obj, att, None)
      d[att] = elem
      if elem is not None and isinstance(elem, datetime.datetime):
        d[att] = elem.isoformat()
    l.append(d)
  return l

def get_orders():
  """Return current user orders."""
  rows = Order.query.filter_by(user_id=current_user.id).\
                     order_by(Order.created.desc()).\
                     limit(app.config['RECENT_ORDERS_SIZE']).all()
  orders = rows_to_dicts(rows, ['id', 'agent', 'type', 'price_open',
                                'volume', 'price_close', 'profit',
                                'closed', 'created'])
  return orders

@app.route('/')
@login_required
def index():
  """Index page."""
  return render_template('index.html')

@socketio.on('connect')
def handle_connect():
  """Handle incoming websocket connection."""
  if not current_user.is_authenticated:
    return False
  # We join a single room to send unique messages
  # based on rooms from server side
  join_room(current_user.username)
  emit('leaderboard', get_leaders())
  emit('orders', get_orders())
  return True

@socketio.on('disconnect')
def handle_disconnect():
  """Handle disconnect of websocket connection."""
  leave_room(current_user.username)

@socketio.on('chat')
def handle_chat(json):
  """Handle incoming chat messages."""
  emit('chat', json, broadcast=True)

@app.route('/trade', methods=['POST'])
@login_required
def trade():
  """Client to broker endpoint."""
  # Pass the trade request to broker
  req = request.json
  agent_name = req.pop('name', 'nobody')
  resp = broker.handle(req)
  if resp['retcode'] == 0 and req['action'] in (2, 3):
    # Record the new order
    order = Order(id=resp['order_id'], user_id=current_user.id,
                  type="BUY" if req['action'] == 2 else "SELL",
                  agent=agent_name, price_open=round(resp['price'], 5),
                  volume=req['volume'])
    db.session.add(order)
    db.session.commit()
    # Send order update
    socketio.emit('order', rows_to_dicts([order], ['id', 'agent', 'type', 'price_open', 'volume',
                                                   'price_close', 'profit', 'closed', 'created'])[0],
                  room=current_user.username)
  elif resp['retcode'] == 0 and req['action'] == 1:
    # Close the recorded order
    order = Order.query.get_or_404(req['order_id'])
    order.price_close = round(resp['price'], 5)
    order.profit = round(resp['profit'], 5)
    order.closed = datetime.datetime.now()
    current_user.balance = round(resp['profit'] + current_user.balance, 5)
    db.session.commit()
    # Send leaderboard update
    socketio.emit('leaderboard', get_leaders())
    # Send order update
    socketio.emit('order', rows_to_dicts([order], ['id', 'agent', 'type', 'price_open', 'volume',
                                                   'price_close', 'profit', 'closed', 'created'])[0],
                  room=current_user.username)
  return jsonify(resp)

def reset_account():
  """Reset current active account."""
  # Delete user orders
  Order.query.filter_by(user_id=current_user.id).delete()
  # Reset balance
  current_user.balance = 0
  db.session.commit()
  app.logger.info("Reset user: %s", current_user.username)
  # Send leaderboard update
  socketio.emit('leaderboard', get_leaders())
  return redirect(url_for('index'))

def delete_account():
  """Delete current active account."""
  user = User.query.get(current_user.id)
  logout_user()
  db.session.delete(user)
  db.session.commit()
  app.logger.info("Delete user: %s", user.username)
  # Send leaderboard update
  socketio.emit('leaderboard', get_leaders())
  return redirect(url_for('login'))

def account_handler(action):
  """Handle account actions."""
  form = UserPasswordForm()
  if form.validate_on_submit():
    # Check username and password again
    if (form.username.data == current_user.username and
        current_user.is_correct_password(form.password.data)):
      # Attempt to close any open orders first
      orders = Order.query.filter_by(user_id=current_user.id, closed=None).all()
      for order in orders:
        r = broker.talk(order_id=order.id, action=1)
        if r['retcode'] != 0:
          app.logger.error("Could not close %s order: %s", action, order.id)
      # Perform requests account action
      if action == "account_reset":
        return reset_account()
      if action == "account_delete":
        return delete_account()
    return redirect(url_for(action))
  return render_template('account.html', form=form,
                         form_header=action.replace('_', ' ').title())

@app.route('/account_reset', methods=['GET', 'POST'])
@login_required
def account_reset():
  """Handler for account reset."""
  return account_handler("account_reset")

@app.route('/account_delete', methods=['GET', 'POST'])
@login_required
def account_delete():
  """Handler for account delete."""
  return account_handler("account_delete")

@app.route('/logout')
def logout():
  """Logout and redirect user."""
  logout_user()
  return redirect(url_for('login'))
