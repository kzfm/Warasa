from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
from database import db_session

DEBUG      = True
SECRET_KEY = 'echo inada'
USERNAME   = 'admin'
PASSWORD   = 'default'

app = Flask(__name__)
app.config.from_object(__name__)

@app.after_request
def after_request(response):
    db_session.remove()
    return response

@app.route('/')
def show_entries():
    return render_template('show_entries.html', entries=[])

# @app.route('/add', methods=['POST'])
# def add_entry():
#     if not session.get('logged_in'):
#         abort(401)
#     g.db.execute('insert into entries (title, text) values (?, ?)',
#                  [request.form['title'], request.form['text']])
#     g.db.commit()
#     return redirect(url_for('show_entries'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        user  = db_session.query(Tag).filter(User.name == request.form['username']).filter(User.password == request.form['password']).first()
        if  user == None:
            error = 'Invalid username or password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('show_entries'))
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('show_entries'))

if __name__ == '__main__':
    app.run()
