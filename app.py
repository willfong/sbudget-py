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
DATABASE=os.path.join(app.root_path, 'sbudget.db')

def connect_db():
    rv = sqlite3.connect(DATABASE)
    rv.row_factory = sqlite3.Row
    return rv

def get_db():
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

def formatMoney(amount, decimalPlaces, displayCurrency):
    return '{c}{0:.{p}f}'.format(round(amount, decimalPlaces), p = decimalPlaces, c = displayCurrency)

@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

@app.route('/')
def index():
    db = get_db()
    cur = db.execute('SELECT exchangeRate FROM settings')
    exchangeRate = cur.fetchall()[0][0]
    if exchangeRate != 1:
        flash('Exchange rate enabled: 1 home currency = {} local currency'.format(exchangeRate), 'warning')
    cur = db.execute('SELECT id, name FROM types')
    types = cur.fetchall()
    cur = db.execute('SELECT e.id AS id, e.date AS date, t.name AS name, e.amount AS amount FROM entries AS e INNER JOIN types AS t ON e.type = t.id ORDER BY e.id DESC LIMIT 5')
    last5 = cur.fetchall()
    return render_template('index.html', types=types, last5=last5)

@app.route('/addAmount', methods=['POST'])
def addAmount():
    db = get_db()
    cur = db.execute('SELECT decimalPlaces, exchangeRate FROM settings')
    decimalPlaces, exchangeRate = cur.fetchall()[0]
    if exchangeRate != 1:
        amount = round( float(request.form['amount']) * (1.0 / exchangeRate), decimalPlaces )
    else:
        print "No exchange rate found"
        amount = request.form['amount']

    db.execute('INSERT INTO entries (date, monthcode, daycode, type, amount) VALUES (?,?,?,?,?)',
      [request.form['date'], request.form['monthcode'], request.form['daycode'], request.form['type'], amount])
    db.commit()
    cur = db.execute('SELECT name FROM types WHERE id = ?', [request.form['type']])
    typeName = cur.fetchall()[0][0]
    flash('{} added to {}'.format(amount, typeName))
    return redirect(url_for('index'))

@app.route('/report')
def report():
    monthcode = time.strftime("%Y%m")
    daycode = time.strftime("%d")
    daysleft = int(monthrange(int(time.strftime("%Y")), int(time.strftime("%m")))[1]) - int(time.strftime("%d"))
    if daysleft == 0:
        daysleft = 1
    db = get_db()
    cur = db.execute('SELECT * FROM settings');
    settings = cur.fetchall()[0]
    monthBudget = settings['monthlyBudget']
    cur = db.execute('SELECT SUM(amount) AS total FROM entries WHERE monthcode = ?', [monthcode]);
    monthSpent = cur.fetchone()['total'] or 0
    cur = db.execute('SELECT SUM(amount) AS total FROM entries WHERE monthcode = ?', [monthcode]);
    dailyAvgSpent = float( cur.fetchone()['total'] or 0 ) / float(daycode)
    monthLeft = monthBudget - monthSpent
    dailyAvgFuture = monthLeft / daysleft
    report = {
      "monthbudget": formatMoney(monthBudget, settings["decimalPlaces"], settings["displayCurrency"]),
      "monthspent": formatMoney(monthSpent, settings["decimalPlaces"], settings["displayCurrency"]),
      "monthleft": formatMoney(monthLeft, settings["decimalPlaces"], settings["displayCurrency"]),
      "dailyavgspent": formatMoney(dailyAvgSpent, settings["decimalPlaces"], settings["displayCurrency"]),
      "daysleft": daysleft,
      "dailyavgfuture": formatMoney(dailyAvgFuture, settings["decimalPlaces"], settings["displayCurrency"])
    }
    cur = db.execute('SELECT e.date AS date, t.name AS name, e.amount AS amount FROM entries AS e INNER JOIN types AS t ON e.type = t.id WHERE monthcode = ? ORDER BY e.id DESC', [monthcode])
    lastLog = cur.fetchall()
    return render_template('report.html', report=report, lastLog=lastLog, settings=settings)

@app.route('/settings')
def settings():
    db = get_db()
    cur = db.execute('SELECT monthlyBudget, decimalPlaces, displayCurrency, exchangeRate FROM settings');
    settings = cur.fetchall()
    return render_template('settings.html', settings=settings[0])

@app.route('/settigs/update', methods=['POST'])
def settingsUpdate():
    db = get_db()
    if request.form['monthlyBudget']:
        db.execute('UPDATE settings SET monthlyBudget = ?', [request.form['monthlyBudget']])
    if request.form['decimalPlaces']:
        db.execute('UPDATE settings SET decimalPlaces = ?', [request.form['decimalPlaces']])
    if request.form['displayCurrency']:
        db.execute('UPDATE settings SET displayCurrency = ?', [request.form['displayCurrency']])
    if request.form['exchangeRate']:
        db.execute('UPDATE settings SET exchangeRate = ?', [request.form['exchangeRate']])

    db.commit()
    return redirect(url_for('report'))
