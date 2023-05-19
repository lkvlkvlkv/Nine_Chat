from model import Session, User
import bcrypt

def check_user(username,email,password,confirm_password):
    name_err = check_username(username)
    if name_err:
        return name_err
    email_err = check_email(email)
    if email_err:
        return email_err
    password_err = check_password(password,confirm_password)
    if password_err:
        return password_err
    return None

def check_username(username):
    if username == None or username == "":
        return "Username can't be null!"
    session = Session()
    check_user = session.query(User).filter(User.username == username).first()
    if check_user != None:
        return "Username has been used!"
    return None

def valid_email(email):
    import re
    regex = re.compile(r'([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+')
    if re.fullmatch(regex, email):
        return None
    else:
        return "Invalid Email"

def check_email(email):
    session = Session()
    check_user = session.query(User).filter(User.email == email).first()
    if check_user != None:
        return "Email has been used!"
    return valid_email(email)

def check_password(password, confirm_password):
    if password == None or password == "":
        return "Password can't be null!"
    if password != confirm_password:
        return "Two passwords you entered do not match."

def generate_friend_code():
    import random, string
    friend_code = ''.join(random.choice(
        string.ascii_letters + string.digits) for x in range(6))
    while check_friend_code_repeat(friend_code):
        friend_code = ''.join(random.choice(
            string.ascii_letters + string.digits) for x in range(6))
    return friend_code

def check_friend_code_repeat(friend_code):
    from model import Session, User, engine
    session = Session()
    check_user = session.query(User).filter(
        User.friend_code == friend_code).first()
    return check_user != None

def login_user(account,password,account_type):
    user = None
    session = Session()
    if account_type == 'username':
        user = session.query(User).filter(User.username == account).first()
    else:
        user = session.query(User).filter(User.email == account).first()
    if user != None and bcrypt.checkpw(password.encode('utf-8') ,user.password):
        return user.nine_id
    return -1

