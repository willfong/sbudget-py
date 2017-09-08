import os
import sqlite3
import string
import random
import time
from calendar import monthrange
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash
app = Flask(__name__)
app.config.from_object(__name__)

app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'sbudget.db'),
    SECRET_KEY=''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(32)),
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
    cur = db.execute('SELECT e.id AS id, e.date AS date, t.name AS name, e.amount AS amount FROM entries AS e INNER JOIN types AS t ON e.type = t.id ORDER BY e.date DESC LIMIT 5')
    last5 = cur.fetchall()
    return render_template('index.html', types=types, last5=last5)

@app.route('/addAmount', methods=['POST'])
def addAmount():
    db = get_db()
    db.execute('INSERT INTO entries (date, monthcode, daycode, type, amount) VALUES (?,?,?,?,?)',
      [request.form['date'], request.form['monthcode'], request.form['daycode'], request.form['type'], request.form['amount']])
    db.commit()
    cur = db.execute('SELECT name FROM types WHERE id = ?', [request.form['type']])
    typeName = cur.fetchall()[0][0]
    flash('{} added to {}'.format(request.form['amount'], typeName))
    return redirect(url_for('index'))

@app.route('/report')
def report():
    monthcode = time.strftime("%Y%m")
    daycode = time.strftime("%d")
    daysleft = int(monthrange(int(time.strftime("%Y")), int(time.strftime("%m")))[1]) - int(time.strftime("%d"))
    db = get_db()
    cur = db.execute('SELECT * FROM settings');
    settings = cur.fetchall()
    monthBudget = settings[0]['monthlyBudget']
    cur = db.execute('SELECT SUM(amount) AS total FROM entries WHERE monthcode = ?', [monthcode]);
    monthSpent = cur.fetchone()['total'] or 0
    cur = db.execute('SELECT SUM(amount) AS total FROM entries WHERE monthcode = ?', [monthcode]);
    dailyAvgSpent = float( cur.fetchone()['total'] or 0 ) / float(daycode)
    monthLeft = monthBudget - monthSpent
    dailyAvgFuture = monthLeft / daysleft
    report = {
      "monthbudget": monthBudget,
      "monthspent": monthSpent,
      "monthleft": monthLeft,
      "dailyavgspent": dailyAvgSpent,
      "daysleft": daysleft,
      "dailyavgfuture": dailyAvgFuture
    }
    cur = db.execute('SELECT e.date AS date, t.name AS name, e.amount AS amount FROM entries AS e INNER JOIN types AS t ON e.type = t.id WHERE monthcode = ? ORDER BY e.date DESC', [monthcode])
    lastLog = cur.fetchall()
    return render_template('report.html', report=report, lastLog=lastLog)

@app.route('/settings')
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
