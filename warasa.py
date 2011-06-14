#!/usr/bin/env python
# -*- encoding:utf-8 -*-

from flask import Flask, request, session, g, \
    redirect, url_for, abort, render_template, flash, jsonify
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


@app.route('/entries/new', methods=['GET'])
def new_entry(doi=None):
    if doi == None:
        return render_template('entry_form.html')

@app.route('/entries/<path:doi>', methods=['GET'])
@app.route('/entries/', methods=['GET'])
def show_entry(doi=None):
    if doi == None:
        return render_template('entry_form.html')

    entry = db_session.query(Entry).filter(Entry.doi == doi).first()

    if entry == None:
        abort(404)
    else:
        return render_template('show_entry.html', entry=entry)


@app.route('/entries/<path:doi>', methods=['POST'])
@app.route('/entries/', methods=['POST'])
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


@app.route('/bookmarks/<string:hash>', methods=['GET', 'POST'])
def show_bookmark(hash=None):
    if id == None:
        abort(404)

    bookmark = db_session.query(Bookmark).filter(Bookmark.hash == hash).first()

    if bookmark == None:
        abort(404)
    else:
        return render_template('show_bookmark.html', bookmark=bookmark)


@app.route('/bookmarks/', methods=['GET', 'POST'])
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

### API ###

# --- Entry --- #
# GET /v1/entries/         -> list
# GET /v1/entries/<doi>    -> show entry
# POST /v1/entries         -> new entry
# DELETE /v1/entries/<doi> -> delete entry
# --- not yet ---
# PUT /v1/entries/<doi>    -> edit entry


@app.route('/v1/entries/<path:doi>', methods=['GET'])
@app.route('/v1/entries/', methods=['GET'])
def _show_entry(doi=None):
    if doi == None:
        entries = []
        for entry in db_session.query(Entry).all():
            entries.append({ 'title' : entry.title, 
                             'abstract' : entry.abstract,
                             'doi' : entry.doi,
                             'pubmed_id' : entry.pubmed_id
                             })
        return jsonify(entries=entries)
    else:
        entry = db_session.query(Entry).filter(Entry.doi == doi).first()

        if entry == None:
            abort(404)

        return jsonify(title = entry.title, 
                       abstract = entry.abstract,
                       doi = entry.doi,
                       pubmed_id = entry.pubmed_id
                       )


@app.route('/v1/entries', methods=['POST'])
def _add_entry():
    if request.form['doi'] == None:
        abort(404)
    else:
        ref = get_contents(request.form['doi'])

        entry = Entry()
        entry.title = ref['title']
        entry.doi = ref['doi']
        entry.abstract = ref['abstract']
        db_session.add(entry)
        db_session.commit()

        return jsonify(title = entry.title, 
                       abstract = entry.abstract,
                       doi = entry.doi,
                       pubmed_id = entry.pubmed_id
                       )


@app.route('/v1/entries/<path:doi>', methods=['DELETE'])
def _delete_entry():
    if request.form['doi'] == None:
        abort(404)
    else:
        entry = db_session.query(Entry).filter(Entry.doi == doi).first()

        if entry == None:
            abort(404)

        db_session.delete(entry)
        db_session.commit()

    return jsonify(data = "data removed")


# --- Bookmark --- #
# GET /v1/bookmarks/                -> list
# GET /v1/bookmarks/<user>/         -> show user list
# GET /v1/bookmarks/<user>/<doi>    -> show user bookmark
# POST /v1/bookmarks/<user>         -> new bookmark
# DELETE /v1/bookmarks/<user>/<doi> -> delete bookmark
# --- not yet ---
# PUT /v1/bookmarks/<user>/<doi>    -> edit bookmark

@app.route('/v1/bookmarks/<string:user>/<path:doi>', methods=['GET'])
@app.route('/v1/bookmarks/<string:user>', methods=['GET'])
@app.route('/v1/bookmarks/', methods=['GET'])
def _show_bookmark(user=None, doi=None):
    if user == None:
        # todo 後で実装
        abort(404)
    if doi == None:
        # todo 後で実装
        abort(404)
    else:
        bookmark = db_session.query(Bookmark).join(Entry).join(User).filter(
            and_(User.name == user,
                 Entry.doi == doi)
            ).first()

        if bookmark == None:
            abort(404)
        else:
            return jsonify(comment = bookmark.comment)


@app.route('/v1/bookmarks/<string:user>', methods=['POST'])
def _add_bookmark():
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

    return jsonify(comment = bookmark.comment)


@app.route('/v1/bookmarks/<string:user>/<path:doi>', methods=['DELETE'])
def _delete_bookmarks():
    # todo: session check
    user = session['user_name']

    if request.form['doi'] == None:
        abort(404)
    else:
        bookmark = db_session.query(Bookmark).join(Entry).join(User).filter(
            and_(User.name == user,
                 Entry.doi == doi)
            ).first()

        if bookmark == None:
            abort(404)

        db_session.delete(bookmark)
        db_session.commit()

    return jsonify(data = "data removed")


# --- comment --- #
# GET /v1/comments/<user>/<doi>/ -> show comments
# POST /v1/comments/<user>/<doi> -> post new comments
# DELETE /v1/comments/<user>/<doi>/<id>       -> delete comments

@app.route('/v1/comments/<string:user>/<path:doi>/', methods=['GET'])
def _show_comment(user=None,doi=None):
    user_id = session['user_id']
    comment_data = request.form['comment']

    comments = db_session.query(Comment).join(Bookmark).join(User).filter(
        and_(User.name == user,
             Bookmark.doi == doi)
        ).all()

    result = []
    for comment in comments:
        result.append({ 'user': comment.user.name, 'comment' :  comment.comment })

    return jsonify(result)


@app.route('/v1/comments/<string:user>/<path:doi>', methods=['POST'])
def _add_comment(user=None,doi=None):
    user_id = session['user_id']
    bookmark_hash = request.form['bookmark_hash']
    comment_data = request.form['comment']

    bookmark_id = db_session.query(Bookmark).filter(
        Bookmark.hash == bookmark_hash).first().id

    comment = Comment(user_id, bookmark_id, comment_data)
    db_session.add(comment)
    db_session.commit()

    return jsonify(comment = comment_data)


@app.route('/v1/comments/<string:user>/<path:doi>/<int:id>', methods=['DELETE'])
def _delete_comment(user=None,doi=None,id=None):
    comment = db_session.query(Comment).join(Bookmark).join(User).filter(
        and_(User.name == user,
             Bookmark.doi == doi,
             Comment.id == id)
        ).first()

    if comment == None:
        abort(404)
    
    db_session.delete(bookmark)
    db_session.commit()

    return jsonify(data = "data removed")


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


if __name__ == '__main__':
    app.run()
