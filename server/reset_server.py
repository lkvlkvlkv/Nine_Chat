from model import Base, Session, engine, User
import bcrypt
from server import imagedir
import shutil
import os


session = Session(bind=engine)

def init():
    if os.path.isdir(imagedir):
        shutil.rmtree(imagedir)
        os.mkdir(imagedir)

    for i in range(1,11):
        name = "LKV" + str(i)
        new_user = User(username=name,email=name+"@gmail.com",password=bcrypt.hashpw(name.encode('utf8'), bcrypt.gensalt()),friend_code=name)
        session.add(new_user)
        session.commit()

if __name__ == "__main__":
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    init()