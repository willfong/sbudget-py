import os
import sqlite3
import string
import random
import time
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

def read_db(query, args=(), one=False):
    try:
        cur = get_db().execute(query, args)
        rv = cur.fetchall()
        cur.close()
        return (rv[0] if rv else None) if one else rv
    except sqlite3.OperationalError as err:
        print "Database Error: {}".format(err)

def write_db(query, args=()):
    try:
        get_db().cursor().execute(query, args)
        get_db().commit()
    except sqlite3.OperationalError as err:
        print "Database Error: {}".format(err)

def formatMoney(amount, decimalPlaces, displayCurrency):
    return '{c}{0:.{p}f}'.format(round(amount, decimalPlaces), p = decimalPlaces, c = displayCurrency)

@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

@app.route('/')
def index():
    query = ("SELECT exchangeRate FROM settings")
    exchangeRate = read_db(query, one=True)[0]
    if exchangeRate != 1:
        flash('Exchange rate enabled: 1 home currency = {} local currency'.format(exchangeRate), 'warning')
    query = ("SELECT id, name FROM types")
    types = read_db(query)
    query = ("SELECT e.id AS id, e.date AS date, t.name AS name, e.amount AS amount FROM entries AS e INNER JOIN types AS t ON e.type = t.id ORDER BY e.id DESC LIMIT 5")
    last5 = read_db(query)
    return render_template('index.html', types=types, last5=last5)

@app.route('/addAmount', methods=['POST'])
def addAmount():
    query = ("SELECT decimalPlaces, exchangeRate FROM settings")
    decimalPlaces, exchangeRate = read_db(query, one=True)
    if exchangeRate != 1:
        amount = round(float(request.form['amount']) * (1.0 / exchangeRate), decimalPlaces)
    else:
        amount = request.form['amount']
    query = ("INSERT INTO entries (date, monthcode, daycode, type, amount) VALUES (?,?,?,?,?)")
    args = (request.form['date'], request.form['monthcode'], request.form['daycode'], request.form['type'], amount)
    write_db(query, args)
    query = ("SELECT name FROM types WHERE id = ?")
    args = (request.form['type'])
    typeName = read_db(query, args, one=True)[0]
    flash("{} added to {}".format(amount, typeName))
    return redirect(url_for('index'))

@app.route('/report')
def report():
    monthcode = time.strftime("%Y%m")
    daycode = time.strftime("%d")
    daysleft = int(monthrange(int(time.strftime("%Y")), int(time.strftime("%m")))[1]) - int(time.strftime("%d"))
    if daysleft == 0:
        daysleft = 1
    query = ("SELECT monthlyBudget, decimalPlaces, displayCurrency, exchangeRate FROM settings")
    monthBudget, decimalPlaces, displayCurrency, exchangeRate = read_db(query, one=True)
    query = ("SELECT SUM(amount) AS total FROM entries WHERE monthcode = ?")
    args = (monthcode,)
    print monthcode
    monthSpent = read_db(query, args, one=True)[0] or 0
    query = ("SELECT SUM(amount) AS total FROM entries WHERE monthcode = ?")
    args = (monthcode,)
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
    query = ("SELECT e.date AS date, t.name AS name, e.amount AS amount FROM entries AS e INNER JOIN types AS t ON e.type = t.id WHERE monthcode = ? ORDER BY e.id DESC")
    args = (monthcode,)
    lastLog = read_db(query, args)
    return render_template('report.html', report=report, lastLog=lastLog, settings=settings)

@app.route('/settings')
def settings():
    query = ("SELECT monthlyBudget, decimalPlaces, displayCurrency, exchangeRate FROM settings")
    settings = read_db(query)
    return render_template('settings.html', settings=settings[0])

@app.route('/settigs/update', methods=['POST'])
def settingsUpdate():
    if request.form['monthlyBudget']:
        query = ("UPDATE settings SET monthlyBudget = ?")
        args = (request.form['monthlyBudget'],)
        write_db(query, args)
    if request.form['decimalPlaces']:
        query = ("UPDATE settings SET decimalPlaces = ?")
        args = (request.form['decimalPlaces'],)
        write_db(query, args)
    if request.form['displayCurrency']:
        query = ("UPDATE settings SET displayCurrency = ?")
        args = (request.form['displayCurrency'],)
        write_db(query, args)
    if request.form['exchangeRate']:
        query = ("UPDATE settings SET exchangeRate = ?")
        args = (request.form['exchangeRate'],)
        write_db(query, args)
    return redirect(url_for('report'))
