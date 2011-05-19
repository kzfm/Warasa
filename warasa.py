from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
from database import db_session
from models import User, Entry
from sqlalchemy.sql.expression import and_

DEBUG      = True
SECRET_KEY = 'echo inada'

app = Flask(__name__)
app.config.from_object(__name__)

@app.after_request
def after_request(response):
    db_session.remove()
    return response

@app.route('/')
def show_entries():
    entries = db_session.query(Entry).all()
    return render_template('show_entries.html', entries=entries)

# @app.route('/add', methods=['POST'])
# def add_entry():
#     if not session.get('logged_in'):
#         abort(401)
#     g.db.execute('insert into entries (title, text) values (?, ?)',
#                  [request.form['title'], request.form['text']])
#     g.db.commit()
#     return redirect(url_for('show_entries'))

#### user settings ####

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        user  = db_session.query(User).filter(User.name == request.form['username']).first()
        if user != None:
            error = "User is always exists."
        elif request.form['password'] != request.form['password']:
            error = "password didn't match"
        else:
            user = User()
            user.name = request.form['username']
            user.password = request.form['password']
            db_session.add(user)
            db_session.commit()
            session['logged_in'] = True
            session['name'] = user.name
            flash('You were registerd')
            return redirect(url_for('show_entries'))

    return render_template('register.html', error=error)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    error = None
    return render_template('settings.html', error=error)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if  user == None:
            error = 'Invalid username or password'
        else:
            session['logged_in'] = True
            session['name'] = user.name
            flash('You were logged in')
            return redirect(url_for('show_entries'))
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('name', None)
    flash('You were logged out')
    return redirect(url_for('show_entries'))

if __name__ == '__main__':
    app.run()
