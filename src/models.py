from sqlalchemy import *
from sqlalchemy import create_engine, func
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import sessionmaker, relationship, backref, contains_eager, scoped_session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property
from itsdangerous import URLSafeTimedSerializer
from datetime import datetime
import random

#login_serializer = URLSafeTimedSerializer(app.secret_key)
metadata = MetaData()
Base = declarative_base(metadata=metadata)
engine = create_engine('postgresql://postgres:biken1992@localhost:5432/urlaubskalender', echo=True)
Sess = scoped_session(sessionmaker(bind=engine))
sess = Sess()


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True)
    password = Column(String(255))
    name = Column(String(255))
    timestamp = Column(DateTime())


class Categeory(Base):
    __tablename__ = 'categories'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    name = Column(String(255))
    value = Column(Integer)
    timestamp = Column(DateTime())


class Day(Base):
    __tablename__ = 'days'
    id = Column(Integer, primary_key=True)
    day = Column(Integer)
    month = Column(Integer)
    year = Column(Integer)
    category = Column(Integer)
    user = Column(Integer)
    name = Column(String(255))

Base.metadata.create_all(engine)