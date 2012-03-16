#!/usr/bin/env python
# -*- encoding:utf-8 -*-

import os
from flask import Flask, request, session, g, \
    redirect, url_for, abort, render_template, flash, jsonify
from flaskext.openid import OpenID
from flaskext.sqlalchemy import SQLAlchemy

from database import db_session
from models import User, Entry, Bookmark, Comment
from sqlalchemy.sql.expression import and_
from doi import get_contents
from  werkzeug.urls import url_quote_plus

DEBUG = True
SECRET_KEY = 'echo inada'

app = Flask(__name__)
app.config.from_object(__name__)

# settings for jinja
app.jinja_env.filters['urlencode'] = url_quote_plus
app.jinja_env.add_extension('pyjade.ext.jinja.PyJadeExtension')

# database settings
databese_file = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'warasa.db')
db = SQLAlchemy(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///%s' % databese_file

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60))
    email = db.Column(db.String(200))
    openid = db.Column(db.String(200))

    def __init__(self, name, email, openid):
        self.name = name
        self.email = email
        self.openid = openid

# OpenID settings
oid = OpenID(app, os.path.join(os.path.dirname(__file__), 'openid'))


@app.before_request
def lookup_current_user():
    g.user = None
    if 'openid' in session:
        g.user = User.query.filter_by(openid=session['openid']).first()

@app.after_request
def after_request(response):
    db_session.remove()
    return response


@app.route('/')
def show_bookmarks():
    bookmarks = db_session.query(Bookmark).all()
    return render_template('show_bookmarks.html', bookmarks=bookmarks)


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


@app.route('/entries', methods=['POST'])
def add_entry(doi=None):
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
            entries.append({'title': entry.title,
                             'abstract': entry.abstract,
                             'doi': entry.doi,
                             'pubmed_id': entry.pubmed_id
                             })
        return jsonify(entries=entries)
    else:
        entry = db_session.query(Entry).filter(Entry.doi == doi).first()

        if entry == None:
            abort(404)

        return jsonify(title=entry.title,
                       abstract=entry.abstract,
                       doi=entry.doi,
                       pubmed_id=entry.pubmed_id)


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

        return jsonify(title=entry.title,
                       abstract=entry.abstract,
                       doi=entry.doi,
                       pubmed_id=entry.pubmed_id
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

    return jsonify(data="data removed")


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
            return jsonify(comment=bookmark.comment)


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

    return jsonify(comment=bookmark.comment)


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

    return jsonify(data="data removed")


# --- comment --- #
# GET /v1/comments/<user>/<doi>/ -> show comments
# POST /v1/comments/<user>/<doi> -> post new comments
# DELETE /v1/comments/<user>/<doi>/<id>       -> delete comments

@app.route('/v1/comments/<string:user>/<path:doi>/', methods=['GET'])
def _show_comment(user=None, doi=None):
    user_id = session['user_id']
    comment_data = request.form['comment']

    comments = db_session.query(Comment).join(Bookmark).join(User).filter(

        and_(User.name == user,
             Bookmark.doi == doi)
        ).all()

    result = []
    for comment in comments:
        result.append({'user': comment.user.name, 'comment': comment.comment})

    return jsonify(result)


@app.route('/v1/comments/<string:user>/<path:doi>', methods=['POST'])
def _add_comment(user=None, doi=None):
    user_id = session['user_id']
    bookmark_hash = request.form['bookmark_hash']
    comment_data = request.form['comment']

    bookmark_id = db_session.query(Bookmark).filter(
        Bookmark.hash == bookmark_hash).first().id

    comment = Comment(user_id, bookmark_id, comment_data)
    db_session.add(comment)
    db_session.commit()

    return jsonify(comment=comment_data)


@app.route('/v1/comments/<string:user>/<path:doi>/<int:id>', methods=['DELETE'])
def _delete_comment(user=None, doi=None, id=None):
    comment = db_session.query(Comment).join(Bookmark).join(User).filter(
        and_(User.name == user,
             Bookmark.doi == doi,
             Comment.id == id)
        ).first()

    if comment == None:
        abort(404)

    db_session.delete(bookmark)
    db_session.commit()

    return jsonify(data="data removed")


#### user settings ####

@app.route('/login', methods=['GET', 'POST'])
@oid.loginhandler
def login():
    if g.user is not None:
        return redirect(oid.get_next_url())
    if request.method == 'POST':
        openid = request.form.get('openid')
        if openid:
            return oid.try_login(openid, ask_for=['email', 'fullname', 'nickname'])
    return render_template('login.jade', next=oid.get_next_url(),
                           error=oid.fetch_error())

@oid.after_login
def create_or_login(resp):
    session['openid'] = resp.identity_url
    user = User.query.filter_by(openid=resp.identity_url).first()
    if user is not None:
        flash(u'Successfully signed in')
        g.user = user
        return redirect(oid.get_next_url())
    return redirect(url_for('create_profile', next=oid.get_next_url(),
                            name=resp.fullname or resp.nickname,
                            email=resp.email))

@app.route('/create-profile', methods=['GET', 'POST'])
def create_profile():
    if g.user is not None or 'openid' not in session:
        return redirect(url_for('index'))
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        if not name:
            flash(u'Error: you have to provide a name')
        elif '@' not in email:
            flash(u'Error: you have to enter a valid email address')
        else:
            flash(u'Profile successfully created')
            db.session.add(User(name, email, session['openid']))
            db.session.commit()
            return redirect(oid.get_next_url())
    return render_template('create_profile.jade', next_url=oid.get_next_url())

@app.route('/logout')
def logout():
    session.pop('openid', None)
    flash(u'You were signed out')
    return redirect(oid.get_next_url())

if __name__ == '__main__':
    app.run()
