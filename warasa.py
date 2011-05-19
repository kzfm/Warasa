from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
from database import db_session
from models import User, Entry, Bookmark
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
    bookmarks = db_session.query(Bookmark).all()
    return render_template('show_entries.html', bookmarks=bookmarks)

@app.route('/home')
def show_my_entries():
    bookmarks = db_session.query(Bookmark).filter(Bookmark.user.name == session['name']).all()
    return render_template('show_entries.html', bookmarks=bookmarks)

@app.route('/entry/<path:doi>')
def show_entry(doi=None):
    if doi == None: abort(404)

    entry = db_session.query(Entry).filter(Entry.doi == doi).first()

    if entry == None: 
        abort(404)
    else:
        return render_template('show_entry.html', entry=entry)

@app.route('/bookmark/<int:id>')
def show_bookmark(id=None):
    if id == None: abort(404)

    bookmark = db_session.query(Bookmark).filter(Bookmark.id == id).first()

    if bookmark == None: 
        abort(404)
    else:
        return render_template('show_bookmark.html', bookmark=bookmark)

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

#@app.route('/stats/<username>')
#@app.route('/stats/')
#def stats():
#    error = None
#    return render_template('settings.html', error=error)


if __name__ == '__main__':
    app.run()
