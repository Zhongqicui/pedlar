"""Endpoints for the web application."""
import datetime

from flask import render_template, redirect, url_for, request, jsonify
from flask_login import login_user, login_required, current_user, logout_user

from . import app, db, broker
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
      else:
        return redirect(url_for('login'))
    else:
      # Create new user
      user = User(username=form.username.data, password=form.password.data)
      db.session.add(user)
      db.session.commit()
      login_user(user)
      app.logger.info("New user: %s", user.username)
      return redirect(url_for('index'))
  return render_template('login.html', form=form)

@app.route('/')
@login_required
def index():
  return render_template('index.html')

@app.route('/trade', methods=['POST'])
@login_required
def trade():
  # Pass the trade request to broker
  req = request.json
  agent_name = req.pop('name', 'nobody')
  resp = broker.handle(req)
  if resp['retcode'] == 0 and req['action'] in (2, 3):
    # Record the new order
    order = Order(id=resp['order_id'], user_id=current_user.id,
                  type="BUY" if req['action'] == 2 else "SELL",
                  price_open=resp['price'])
    db.session.add(order)
    db.session.commit()
  elif resp['retcode'] == 0 and req['action'] == 1:
    # Close the recorded order
    order = Order.query.get(req['order_id'])
    order.price_close = resp['price']
    order.profit = resp['profit']
    order.closed = datetime.datetime.now()
    db.session.commit()
  return jsonify(resp)

@app.route('/logout')
def logout():
  logout_user()
  return redirect(url_for('login'))
