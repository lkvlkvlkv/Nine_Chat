from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column,Integer, String,DateTime
from sqlalchemy import create_engine
from datetime import datetime
import dateutil.tz
import os


BASE_DIR=os.path.dirname(os.path.realpath(__file__))

engine = create_engine('sqlite:///'+os.path.join(BASE_DIR,'database.db'),echo=False)
Base = declarative_base()

Session = scoped_session(sessionmaker(bind=engine))

class User(Base):
    __tablename__ = 'users'
    nine_id=Column(Integer(),primary_key=True)
    username=Column(String(50),nullable=False,unique=True)
    email=Column(String(80),nullable=False,unique=True)
    password=Column(String(80),nullable=False)
    friend_code=Column(String(10),nullable=False,unique=True)

class Latest_Chat(Base):
    __tablename__ = 'latest_chat'
    id=Column(Integer(),primary_key=True)
    nine_id1=Column(Integer(),nullable=False)
    nine_id2=Column(Integer(),nullable=False)
    type=Column(String(5),nullable=False)
    message=Column(String(5000),nullable=False)
    time=Column(DateTime(),default=datetime.now(dateutil.tz.tzlocal()))

    def __repr__(self):
        return f'<nine_id1={self.nine_id1}, nine_id2={self.nine_id2}, type={self.type}, message={self.message}, time={self.time}'
    
    def as_dict(self):
        return '{'+f'\"nine_id1\":{self.nine_id1}, \"nine_id2\":{self.nine_id2}, \"type\":{self.type}, \"message\":\"{self.message}\", \"time\":\"{datetime.strftime(self.time, "%Y-%d-%m %H:%M:%S")}\"'+'}'

class Chat(Base):
    __tablename__ = 'chat'
    id=Column(Integer(),primary_key=True)
    nine_id1=Column(Integer(),nullable=False)
    nine_id2=Column(Integer(),nullable=False)
    type=Column(Integer(),nullable=False)
    message=Column(String(5000),nullable=False)
    time=Column(DateTime(),default=datetime.now(dateutil.tz.tzlocal()))

    def __repr__(self):
        return f'<nine_id1={self.nine_id1}, nine_id2={self.nine_id2}, type={self.type}, message={self.message}, time={self.time}'
    
    def as_dict(self):
        return '{'+f'\"nine_id1\":{self.nine_id1}, \"nine_id2\":{self.nine_id2}, \"type\":{self.type}, \"message\":\"{self.message}\", \"time\":\"{datetime.strftime(self.time, "%Y-%d-%m %H:%M:%S")}\"'+'}'

class Friend(Base):
    __tablename__ = 'friend'
    id=Column(Integer(),primary_key=True)
    nine_id1=Column(Integer(),nullable=False)
    nine_id2=Column(Integer(),nullable=False)
    time=Column(DateTime(),default=datetime.now(dateutil.tz.tzlocal()))

    def __repr__(self):
        return f'<nine_id1={self.nine_id1}, nine_id2={self.nine_id2}, time={self.time}'
    
    def as_dict(self):
        return '{'+f'\"nine_id1\":{self.nine_id1}, \"nine_id2\":{self.nine_id2}, \"time\":\"{datetime.strftime(self.time, "%Y-%d-%m %H:%M:%S")}\"'+'}'