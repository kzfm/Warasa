from sqlalchemy import Column, Integer, String, Text, DateTime, Table, ForeignKey
from database import Base,init_db, db_session
from sqlalchemy.orm import relation, backref, relationship

entry_tags = Table('entry_tags', Base.metadata,
    Column('entry_id', Integer, ForeignKey('entries.id')),
    Column('tag_id', Integer, ForeignKey('tags.id'))
)

class Entry(Base):
    __tablename__    = 'entries'
    id               = Column(Integer, primary_key=True)
    title            = Column(String(256), unique=True)
    pubmed_id        = Column(Integer, unique=True)
    doi              = Column(String(128), unique=True)
    abstract         = Column(Text())
    tags             = relation("Tag", secondary=entry_tags)
    bookmarks        = relationship("Bookmark", backref="entry")
    
class Tag(Base):
    def __init__(self,name):
        self.name = name

    __tablename__ = 'tags'
    id      = Column(Integer, primary_key=True)
    name    = Column(String(128), unique=True)
    entries = relation("Entry", secondary=entry_tags)

class Bookmark(Base):
    __tablename__ = 'bookmarks'
    id       = Column(Integer, primary_key=True)
    comment  = Column(Text())
    entry_id = Column(Integer, ForeignKey('entries.id'))
    user_id  = Column(Integer, ForeignKey('users.id'))
    
class Comment(Base):
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

    for tag in ['test','chemoinformatics','bioinformatics','database','ATD']:
        t = Tag(tag)
        db_session.add(t)
    db_session.commit()
        
