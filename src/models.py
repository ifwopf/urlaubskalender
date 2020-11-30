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
engine = create_engine('postgresql://postgres:dfghp@localhost:5432/urlaubskalender')
#engine = create_engine('postgres://postgres:Dfghc140@calquik.ct58guzxmoql.eu-central-1.rds.amazonaws.com:5432/postgres', echo=True)
#engine = create_engine('postgres://bfnsdjdsjpjxah:2804230acb68e09e908d80e0b47b03697737a5d45b8f58b819c4ea6f8d2dcff0@ec2-54-225-115-177.compute-1.amazonaws.com:5432/d1ue7m4qfl7vg9', echo=True)
Sess = scoped_session(sessionmaker(bind=engine))
sess = Sess()


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True)
    password = Column(String(255))
    name = Column(String(255))
    first = Column(String(255))
    last = Column(String(255))
    timestamp = Column(DateTime())
    userday = relationship("Userday", back_populates="user")
    calenderUser = relationship("CalenderUser", back_populates="user")

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

class Day(Base):
    __tablename__ = 'day'
    id = Column(Integer, primary_key=True)
    day = Column(Integer)
    month = Column(Integer)
    year = Column(Integer)
    weekday = Column(String(15))
    #userday = relationship("Userday", back_populates="day", uselist=False)

class Calender(Base):
    __tablename__ = 'calender'
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    shared = Column(Boolean)
    category = relationship("Category", back_populates="calender")
    userday = relationship("Userday", back_populates="calender")
    calenderUser = relationship("CalenderUser", back_populates="calender")

class Category(Base):
    __tablename__ = 'category'
    id = Column(Integer, primary_key=True)
    cal_id = Column(Integer, ForeignKey('calender.id'))
    name = Column(String(255))
    color = Column(String(55))
    timestamp = Column(DateTime())
    calender = relationship("Calender", back_populates="category")
    userday = relationship("Userday", back_populates="category")

class Userday(Base):
    __tablename__ = 'userday'
    id = Column(Integer, primary_key=True)
    dayID = Column(Integer, ForeignKey('day.id'))
    calID = Column(Integer, ForeignKey('calender.id'))
    catID = Column(Integer, ForeignKey('category.id'))
    userID = Column(Integer, ForeignKey('user.id'))
    value = Column(Float)
    timeStart = Column(DateTime())
    timeEnd = Column(DateTime())
    name = Column(String(255))
    #day = relationship("Day", back_populates="userday",  uselist=False)
    calender = relationship("Calender", back_populates="userday")
    category = relationship("Category", back_populates="userday")
    user = relationship("User", back_populates="userday")


class CalenderUser(Base):
    __tablename__ = 'calenderUser'
    id = Column(Integer, primary_key=True)
    cID = Column(Integer, ForeignKey(('calender.id')))
    uID = Column(Integer, ForeignKey('user.id'))
    accepted = Column(Boolean)
    admin = Column(Boolean)
    calender = relationship("Calender", back_populates="calenderUser")
    user = relationship("User", back_populates="calenderUser")


#sync Cats from Calender
class SyncCatUser(Base):
    __tablename__ = 'sharedCatUsers'
    id = Column(Integer, primary_key=True)
    scID = Column(Integer)
    ucID = Column(Integer)





#Base.metadata.create_all(engine)