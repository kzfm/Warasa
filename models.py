#!/usr/bin/env python
# -*- encoding:utf-8 -*-

# kzfm <kerolinq@gmail.com>

from sqlalchemy import Column, Integer, String, Text, DateTime, Table, ForeignKey
from database import Base, init_db, db_session
from sqlalchemy.orm import relation, backref, relationship
#import hashlib

SALT = 'kzfm'

bookmark_tags = Table('entry_tags', Base.metadata,
    Column('bookmark_id', Integer, ForeignKey('bookmarks.id')),
    Column('tag_id', Integer, ForeignKey('tags.id'))
)


class Entry(Base):
    __tablename__ = 'entries'
    id        = Column(Integer, primary_key=True)
    title     = Column(String(256), unique=True)
    pubmed_id = Column(Integer)
    doi       = Column(String(128), unique=True)
    abstract  = Column(Text())
    bookmarks = relationship("Bookmark", backref="entry")


class Tag(Base):
    def __init__(self, name):
        self.name = name

    __tablename__ = 'tags'
    id        = Column(Integer, primary_key=True)
    name      = Column(String(128), unique=True)
    bookmarks = relation("Bookmark", secondary=bookmark_tags)


class Bookmark(Base):
    def __init__(self, user_id, entry_id, comment):
        self.user_id  = user_id
        self.entry_id = entry_id
        self.comment  = comment

    __tablename__ = 'bookmarks'
    id       = Column(Integer, primary_key=True)
    comment  = Column(Text())
    entry_id = Column(Integer, ForeignKey('entries.id'))
    user_id  = Column(Integer, ForeignKey('users.id'))
    comments = relationship("Comment", backref="bookmark")
    tags     = relation("Tag", secondary=bookmark_tags)


class Comment(Base):
    def __init__(self, user_id, bookmark_id, comment):
        self.comment = comment
        self.bookmark_id = bookmark_id
        self.user_id = user_id

    __tablename__ = 'comments'
    id          = Column(Integer, primary_key=True)
    comment     = Column(Text())
    bookmark_id = Column(Integer, ForeignKey('bookmarks.id'))    
    user_id     = Column(Integer, ForeignKey('users.id'))


class User(Base):
    __tablename__    = 'users'
    id               = Column(Integer, primary_key=True)
    name             = Column(String(256), unique=True)
    password         = Column(String(128))
    bookmarks        = relationship("Bookmark", backref="user")
    comments         = relationship("Comment", backref="user")    


if __name__ == '__main__':
    init_db()

    user = User()
    user.name = 'admin'
    user.password = 'default'
    db_session.add(user)
    db_session.commit()

    user = User()
    user.name = 'user1'
    user.password = 'test'
    db_session.add(user)
    db_session.commit()

    user = User()
    user.name = 'user2'
    user.password = 'test2'
    db_session.add(user)
    db_session.commit()

    entry = Entry()
    entry.title = 'SARANEA: a freely available program to mine structure-activity and structure-selectivity relationship information in compound data sets.'
    entry.pubmed_id        = 20053000
    entry.doi              = '10.1021/ci900416a'
    entry.abstract         = '''We introduce SARANEA, an open-source Java application for interactive exploration
of structure-activity relationship (SAR) and structure-selectivity relationship
(SSR) information in compound sets of any source. SARANEA integrates various SAR 
and SSR analysis functions and utilizes a network-like similarity graph data
structure for visualization. The program enables the systematic detection of
activity and selectivity cliffs and corresponding key compounds across multiple
targets. Advanced SAR analysis functions implemented in SARANEA include, among
others, layered chemical neighborhood graphs, cliff indices, selectivity trees,
editing functions for molecular networks and pathways, bioactivity summaries of
key compounds, and markers for bioactive compounds having potential side effects.
We report the application of SARANEA to identify SAR and SSR determinants in
different sets of serine protease inhibitors. It is found that key compounds can 
influence SARs and SSRs in rather different ways. Such compounds and their
SAR/SSR characteristics can be systematically identified and explored using
SARANEA. The program and source code are made freely available under the GNU
General Public License.'''    
    db_session.add(entry)
    db_session.commit()

    entry = Entry()
    entry.title            = 'Computational analysis of activity and selectivity cliffs.'
    entry.pubmed_id        = 20838966
    entry.doi              = '10.1007/978-1-60761-839-3_4'
    entry.abstract         = '''The exploration of structure-activity relationships (SARs) is a major challenge
in medicinal chemistry and usually focuses on compound potency for individual
targets. However, selectivity of small molecules that are active against related 
targets is another critical parameter in chemical lead optimization. Here, an
integrative approach for the systematic analysis of SARs and
structure-selectivity relationships (SSRs) of small molecules is presented. The
computational methodology is described and a cathepsin inhibitor set is used to
discuss key aspects of the analysis. Combining a numerical scoring scheme and
graphical visualization of molecular networks, the approach enables the
identification of different local SAR and SSR environments. Comparative analysis 
of these environments reveals variable relationships between molecular structure,
potency, and selectivity. Furthermore, key compounds are identified that are
involved in the formation of activity and/or selectivity cliffs and often display
structural features that determine compound selectivity.'''
    db_session.add(entry)
    db_session.commit()

    entry = Entry()
    entry.title            = 'An MCMC algorithm for detecting short adjacent repeats shared by multiple sequences.'
    entry.pubmed_id        = 21551149
    entry.doi              = '10.1093/bioinformatics/btr287'
    entry.abstract         = '''MOTIVATION: Repeats detection problems are traditionally formulated as string
matching or signal processing problems. They cannot readily handle gaps between
repeat units and are incapable of detecting repeat patterns shared by multiple
sequences. This study detects short adjacent repeats with inter-unit insertions
from multiple sequences. For biological sequences, such studies can shed light on
molecular structure, biological function, and evolution. RESULTS: The task of
detecting short adjacent repeats is formulated as a statistical inference problem
by using a probabilistic generative model. An Markov chain Monte Carlo algorithm 
is proposed to infer the parameters in a de novo fashion. Its applications on
synthetic and real biological data show that the new method not only has a
competitive edge over existing methods, but also can provide a way to study the
structure and the evolution of repeat-containing genes. AVAILABILITY: The related
C++ source code and data sets are available at
http://ihome.cuhk.edu.hk/%7Eb118998/share/BASARD.zip. SUPPLEMENTARY INFORMATION: 
Supplementary materials are available at the journal's web site. CONTACT:
xfan@sta.cuhk.edu.hk.'''
    db_session.add(entry)
    db_session.commit()

    for tag in ['test','chemoinformatics','bioinformatics','database','ATD']:
        t = Tag(tag)
        db_session.add(t)
    db_session.commit()

    bookmark = Bookmark(2, 1, u'テストコメント')
    db_session.add(bookmark)
    db_session.commit()

    bookmark = Bookmark(3, 2, u'activity cliffの把握は重要')
    db_session.add(bookmark)
    db_session.commit()

    comment = Comment(3, 2, u'そう思う')
    db_session.add(comment)
    db_session.commit()

    comment = Comment(2, 2, u'そう思うかな')
    db_session.add(comment)
    db_session.commit()

    comment = Comment(3, 2, u'コメントがもう少しうまく扱えるように考える')
    db_session.add(comment)
    db_session.commit()
