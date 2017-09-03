import os
import sqlite3
import string
import random
import time
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash
app = Flask(__name__)
app.config.from_object(__name__)

app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'sbudget.db'),
    SECRET_KEY=''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(32)),
    USERNAME='admin',
    PASSWORD='default'
))
app.config.from_envvar('FLASKR_SETTINGS', silent=True)

def connect_db():
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv

def get_db():
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

@app.route('/')
def index():
    db = get_db()
    cur = db.execute('SELECT id, name FROM types')
    types = cur.fetchall()
    return render_template('index.html', types=types)

@app.route('/addAmount', methods=['POST'])
def addAmount():
    db = get_db()
    db.execute('INSERT INTO entries (date, monthcode, daycode, type, amount) VALUES (?,?,?,?,?)',
      [request.form['date'], request.form['monthcode'], request.form['daycode'], request.form['type'], request.form['amount']])
    db.commit()
    return redirect(url_for('index'))

@app.route('/report')
def report():
    monthcode = time.strftime("%Y%m")
    daycode = time.strftime("%d")
    db = get_db()
    cur = db.execute('SELECT * FROM settings');
    settings = cur.fetchall()
    monthBudget = settings[0]['monthlyBudget']
    cur = db.execute('SELECT SUM(amount) AS total FROM entries WHERE monthcode = ?', [monthcode]);
    monthSpent = cur.fetchone()['total']
    cur = db.execute('SELECT AVG(amount) AS total FROM entries WHERE monthcode = ?', [monthcode]);
    dailyAvgSpent = cur.fetchone()['total']
    report = {
      "monthbudget": monthBudget,
      "monthspent": monthSpent,
      "monthleft": monthBudget-monthSpent,
      "dailyavgspent": dailyAvgSpent
    }
    return render_template('report.html', report=report)

@app.route('/settigs')
def settings():
    db = get_db()
    cur = db.execute('SELECT * FROM settings');
    settings = cur.fetchall()
    return render_template('settings.html', settings=settings[0])

@app.route('/settigs/update', methods=['POST'])
def settingsUpdate():
    db = get_db()
    db.execute('UPDATE settings SET monthlyBudget = ?', [request.form['monthlybudget']])
    db.commit()
    return redirect(url_for('report'))
