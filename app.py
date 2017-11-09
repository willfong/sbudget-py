import os
import sqlite3
import string
import random
import hashlib
import time
from functools import wraps
from calendar import monthrange
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash

app = Flask(__name__)

app.secret_key = os.environ['SECRET_KEY']
DATABASE=os.path.join(app.root_path, 'app.db')

def connect_db():
    rv = sqlite3.connect(DATABASE)
    rv.row_factory = sqlite3.Row
    return rv

def get_db():
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

def read_db(query, params=(), one=False):
    if isinstance(params, tuple):
        args = params
    else:
        args = (params,)
    try:
        cur = get_db().execute(query, args)
        rv = cur.fetchall()
        cur.close()
        return (rv[0] if rv else None) if one else rv
    except sqlite3.OperationalError as err:
        print "Database Error: {}".format(err)

def write_db(query, params=(), last_id=False):
    if isinstance(params, tuple):
        args = params
    else:
        args = (params,)
    try:
        cur = get_db().cursor()
        cur.execute(query, args)
        get_db().commit()
    except sqlite3.Error as err:
        # TODO: need a way to determine operational error
        print "Database Error: {}".format(err)
        return False
    if last_id:
        return cur.lastrowid
    else:
        return True

def formatMoney(amount, decimalPlaces, displayCurrency):
    return '{c}{0:.{p}f}'.format(round(amount, decimalPlaces), p = decimalPlaces, c = displayCurrency)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not 'user_id' in session:
            flash('Please login first', 'warning')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/main')
@login_required
def main():
    query = ("SELECT exchangeRate FROM users WHERE id = ?")
    params = (session['user_id'])
    exchangeRate = read_db(query, params, one=True)[0]
    if exchangeRate != 1:
        flash('Exchange rate enabled: 1 home currency = {} local currency'.format(exchangeRate), 'warning')
    query = ("SELECT id, name FROM types WHERE users_id = ?")
    params = (session['user_id'])
    types = read_db(query, params)
    query = ("SELECT e.id AS id, e.date AS date, t.name AS name, e.amount AS amount FROM entries AS e INNER JOIN types AS t ON e.type = t.id WHERE e.users_id = ? ORDER BY e.id DESC LIMIT 5")
    params = (session['user_id'])
    last5 = read_db(query, params)
    return render_template('main.html', types=types, last5=last5)


@app.route('/addAmount', methods=['POST'])
@login_required
def addAmount():
    query = ("SELECT decimalPlaces, exchangeRate FROM users WHERE id = ?")
    params = (session['user_id'])
    decimalPlaces, exchangeRate = read_db(query, params, one=True)
    if exchangeRate != 1:
        amount = round(float(request.form['amount']) * (1.0 / exchangeRate), decimalPlaces)
    else:
        amount = request.form['amount']
    query = ("INSERT INTO entries (users_id, date, monthcode, daycode, type, amount) VALUES (?, ?,?,?,?,?)")
    args = (session['user_id'], request.form['date'], request.form['monthcode'], request.form['daycode'], request.form['type'], amount)
    write_db(query, args)
    query = ("SELECT name FROM types WHERE id = ? AND users_id = ?")
    args = (request.form['type'], session['user_id'])
    typeName = read_db(query, args, one=True)[0]
    flash("{} added to {}".format(amount, typeName), 'success')
    return redirect(url_for('main'))

@app.route('/report')
@login_required
def report():
    monthcode = time.strftime("%Y%m")
    daycode = time.strftime("%d")
    daysleft = int(monthrange(int(time.strftime("%Y")), int(time.strftime("%m")))[1]) - int(time.strftime("%d"))
    if daysleft == 0:
        daysleft = 1
    query = ("SELECT monthlyBudget, decimalPlaces, displayCurrency, exchangeRate FROM users WHERE id = ?")
    params = (session['user_id'])
    monthBudget, decimalPlaces, displayCurrency, exchangeRate = read_db(query, params, one=True)
    query = ("SELECT SUM(amount) AS total FROM entries WHERE monthcode = ? AND users_id = ?")
    args = (monthcode, session['user_id'])
    monthSpent = read_db(query, args, one=True)[0] or 0
    query = ("SELECT SUM(amount) AS total FROM entries WHERE monthcode = ? AND users_id = ?")
    args = (monthcode, session['user_id'])
    dailyAvgSpent = float(read_db(query, args, one=True)[0] or 0) / float(daycode)
    monthLeft = monthBudget - monthSpent
    dailyAvgFuture = monthLeft / daysleft
    report = {
      "monthbudget": formatMoney(monthBudget, decimalPlaces, displayCurrency),
      "monthspent": formatMoney(monthSpent, decimalPlaces, displayCurrency),
      "monthleft": formatMoney(monthLeft, decimalPlaces, displayCurrency),
      "dailyavgspent": formatMoney(dailyAvgSpent, decimalPlaces, displayCurrency),
      "daysleft": daysleft,
      "dailyavgfuture": formatMoney(dailyAvgFuture, decimalPlaces, displayCurrency)
    }
    query = ("SELECT e.date AS date, t.name AS name, e.amount AS amount FROM entries AS e INNER JOIN types AS t ON e.type = t.id WHERE monthcode = ? AND e.users_id = ? ORDER BY e.id DESC")
    args = (monthcode, session['user_id'])
    lastLog = read_db(query, args)
    return render_template('report.html', report=report, lastLog=lastLog, settings=settings)

@app.route('/settings')
@login_required
def settings():
    query = ("SELECT monthlyBudget, decimalPlaces, displayCurrency, exchangeRate FROM users WHERE id = ?")
    params = (session['user_id'])
    settings = read_db(query, params)
    query = ("SELECT id, name FROM types WHERE users_id = ? ORDER BY name")
    params = (session['user_id'])
    types = read_db(query, params)
    return render_template('settings.html', settings=settings[0], types=types)

@app.route('/settings/addtype', methods=['POST'])
@login_required
def settingsAddType():
    query = ("INSERT INTO types (users_id, name) VALUES (?,?)")
    params = (session['user_id'], request.form['newtype'])
    write_db(query, params)
    flash("New Setting Added: {}".format(request.form['newtype']), 'success')
    return redirect(url_for('settings'))

@app.route('/settigs/update', methods=['POST'])
@login_required
def settingsUpdate():
    if request.form['password']:
        query = ("UPDATE users SET password = ? WHERE id = ?")
        args = (hashlib.sha256(request.form['password']).hexdigest(), session['user_id'])
        write_db(query, args)
    if request.form['monthlyBudget']:
        query = ("UPDATE users SET monthlyBudget = ? WHERE id = ?")
        args = (request.form['monthlyBudget'], session['user_id'])
        write_db(query, args)
    if request.form['decimalPlaces']:
        query = ("UPDATE users SET decimalPlaces = ? WHERE id = ?")
        args = (request.form['decimalPlaces'], session['user_id'])
        write_db(query, args)
    if request.form['displayCurrency']:
        query = ("UPDATE users SET displayCurrency = ? WHERE id = ?")
        args = (request.form['displayCurrency'], session['user_id'])
        write_db(query, args)
    if request.form['exchangeRate']:
        query = ("UPDATE users SET exchangeRate = ? WHERE id = ?")
        args = (request.form['exchangeRate'], session['user_id'])
        write_db(query, args)
    return redirect(url_for('report'))

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        if request.form['action'] == 'login':
            query = ("SELECT id FROM users WHERE username = ? AND password = ?")
            params = (request.form['username'], hashlib.sha256(request.form['password']).hexdigest())
            user = read_db(query, params, one=True)
            if user is None:
                flash('Username/Password not found!', 'danger')
            else:
                session['user_id'] = user['id']
                return redirect(url_for('main'))
        if request.form['action'] == 'create':
            query = ("INSERT INTO users (username, password, monthlyBudget, decimalPlaces, displayCurrency, exchangeRate) VALUES (?,?,?,?,?,?)")
            params = (request.form['username'], hashlib.sha256(request.form['password']).hexdigest(), 1000, 2, '$', 1)
            # TODO: Should refactor this to check for errors
            user_id = write_db(query, params, last_id=True)
            session['user_id'] = user_id
            return redirect(url_for('main'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))
