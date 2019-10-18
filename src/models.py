from sqlalchemy import *
from sqlalchemy import create_engine, func
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import sessionmaker, relationship, backref, contains_eager, scoped_session
from sqlalchemy.ext.declarative import declarative_base
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.ext.hybrid import hybrid_property
from itsdangerous import URLSafeTimedSerializer
from datetime import datetime
import random

#login_serializer = URLSafeTimedSerializer(app.secret_key)
metadata = MetaData()
Base = declarative_base(metadata=metadata)
#postgresql-parallel-70450
#localhost:5432/urlaubskalender
engine = create_engine('postgres://bfnsdjdsjpjxah:2804230acb68e09e908d80e0b47b03697737a5d45b8f58b819c4ea6f8d2dcff0@ec2-54-225-115-177.compute-1.amazonaws.com:5432/d1ue7m4qfl7vg9', echo=True)
Sess = scoped_session(sessionmaker(bind=engine))

sess = Sess()


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True)
    password = Column(String(255))
    name = Column(String(255))
    timestamp = Column(DateTime())

    def __init__(self, email, password):
        self.email = email
        self.password = generate_password_hash(password, method='sha256')

    @classmethod
    def authenticate(cls, **kwargs):
        email = kwargs.get('email')
        password = kwargs.get('password')

        if not email or not password:
            return None

        user = sess.query(cls).filter_by(email=email).first()
        if not user or not check_password_hash(user.password, password):
            return None

        return user

    def to_dict(self):
        return dict(id=self.id, email=self.email)


class Categeory(Base):
    __tablename__ = 'categories'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    name = Column(String(255))
    color = Column(String(55))
    value = Column(Integer)
    timestamp = Column(DateTime())


class Day(Base):
    __tablename__ = 'days'
    id = Column(Integer, primary_key=True)
    day = Column(Integer)
    month = Column(Integer)
    year = Column(Integer)
    weekday = Column(String(15))
    category = Column(Integer)
    user = Column(Integer)
    name = Column(String(255))

#Base.metadata.create_all(engine)