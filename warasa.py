from flask import Flask, request, session, g, \
    redirect, url_for, abort, render_template, flash
from database import db_session
from models import User, Entry, Bookmark, Comment
from sqlalchemy.sql.expression import and_
from doi import get_contents

DEBUG = True
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
    bookmarks = db_session.query(Bookmark).filter(
            Bookmark.user.name == session['name']).all()
    return render_template('show_entries.html', bookmarks=bookmarks)


@app.route('/entry/<path:doi>', methods=['GET'])
@app.route('/entry/', methods=['GET'])
def show_entry(doi=None):
    if doi == None:
        return render_template('entry_form.html')

    entry = db_session.query(Entry).filter(Entry.doi == doi).first()

    if entry == None:
        abort(404)
    else:
        return render_template('show_entry.html', entry=entry)


@app.route('/entry/<path:doi>', methods=['POST'])
@app.route('/entry/', methods=['POST'])
def add_entry(doi=None):
    if doi == None:
        if request.form['doi'] == None:
            return redirect(url_for('show_entry'))
        else:
            ref = get_contents(request.form['doi'])
            entry = Entry()
            entry.title = ref['title']
            entry.doi = ref['doi']
            entry.abstract = ref['abstract']
            db_session.add(entry)
            db_session.commit()

            return redirect(url_for('show_entry', doi=ref['doi']))

    if entry == None:
        abort(404)
    else:
        return render_template('add_entry.html', entry=entry)


@app.route('/bookmark/<string:hash>', methods=['GET', 'POST'])
def show_bookmark(hash=None):
    if id == None:
        abort(404)

    bookmark = db_session.query(Bookmark).filter(Bookmark.hash == hash).first()

    if bookmark == None:
        abort(404)
    else:
        return render_template('show_bookmark.html', bookmark=bookmark)


@app.route('/bookmark/', methods=['GET', 'POST'])
def add_bookmark():
    if request.method == 'POST':
        user_id = session['user_id']

        entry_id = db_session.query(Entry).filter(
            Entry.doi == request.form['doi']).one().id

        app.logger.debug('uid: %s, eid: %s, comment: %s, name: %s' %
                         (user_id, entry_id,
                          request.form['comment'], session['name'])
                         )

        bookmark = Bookmark(user_id, entry_id, request.form['comment'],
                          session['name'], request.form['doi'])
        db_session.add(bookmark)
        db_session.commit()

        return redirect(url_for('show_bookmark', hash=bookmark.hash))
    abort(404)

#### comment ####


@app.route('/comment/add', methods=['GET', 'POST'])
def add_comment():
    if request.method == 'POST':
        user_id = session['user_id']
        bookmark_hash = request.form['bookmark_hash']
        comment_data = request.form['comment']

        bookmark_id = db_session.query(Bookmark).filter(
            Bookmark.hash == bookmark_hash).first().id

        comment = Comment(user_id, bookmark_id, comment_data)
        db_session.add(comment)
        db_session.commit()

        return redirect(url_for('show_bookmark', hash=bookmark_hash))
    abort(404)

#### user settings ####


@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        user = db_session.query(User).filter(
            User.name == request.form['username']).first()

        if user != None:
            error = "User is always exists."
        elif request.form['password'] != request.form['retype_password']:
            error = "password didn't match"
        else:
            user = User()
            user.name = request.form['username']
            user.password = request.form['password']
            db_session.add(user)
            db_session.commit()
            session['logged_in'] = True
            session['name'] = user.name
            session['user_id'] = user.id
            flash('You were registerd')
            return redirect(url_for('show_entries'))

    return render_template('register.html', error=error)


@app.route('/settings', methods=['GET', 'POST'])
def settings():
    error = None
    return render_template('settings.html', error=error)


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        user = db_session.query(User).filter(
            and_(User.name == request.form['username'],
                 User.password == request.form['password'])
            ).first()

        if  user == None:
            error = 'Invalid username or password'
        else:
            session['logged_in'] = True
            session['name'] = user.name
            session['user_id'] = user.id
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
