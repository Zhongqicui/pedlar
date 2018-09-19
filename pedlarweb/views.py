"""Endpoints for the web application."""
from flask import render_template, redirect, url_for, jsonify
from flask_login import login_user, login_required, logout_user

from . import app, db, broker
from .forms import UserPasswordForm
from .models import User

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
        return redirect(url_for('index'))
      else:
        return redirect(url_for('login'))
    else:
      # Create new user
      user = User(username=form.username.data, password=form.password.data)
      db.session.add(user)
      db.session.commit()
      login_user(user)
      return redirect(url_for('index'))
  return render_template('login.html', form=form)

@app.route('/')
@login_required
def index():
  return render_template('index.html')

@app.route('/buy')
@login_required
def buy():
  return jsonify(broker.buy())

@app.route('/logout')
def logout():
  logout_user()
  return redirect(url_for('login'))
