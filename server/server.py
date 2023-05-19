import socket
import json
import bcrypt
from datetime import datetime
from check_error import check_user,generate_friend_code, login_user, valid_email
import threading
import atexit
import os
 
all_thread = []
nine_id_to_socket = {}
chat_id_to_socket = {}
basedir = os.path.abspath(os.path.dirname(__file__))
imagedir = os.path.join(basedir, 'image_message')

def send_to_client(server, dic):
    print("server send", dic)
    for key in dic:
        if isinstance(dic[key], str):
            dic[key] = dic[key].replace("'", "~!@#$%^&*()~!@#$%^&*(~!@#$%^&*")
            dic[key] = dic[key].replace('"', ')(*&^%$#@!)(*&^%$#@!(*&^%$#@!~')
        if isinstance(dic[key], list):
            for dic2 in dic[key]:
                for key2 in dic2:
                    if isinstance(dic2[key2], str):
                        dic2[key2] = dic2[key2].replace("'", "~!@#$%^&*()~!@#$%^&*(~!@#$%^&*")
                        dic2[key2] = dic2[key2].replace('"', ')(*&^%$#@!)(*&^%$#@!(*&^%$#@!~')
    print(dic)
    dic = str(dic)
    dic = dic.replace("'", "\"")
    json_msg = json.loads(dic)
    server.sendall(str(json_msg).encode())

def add_friend(dic):
    from model import Session, User, Friend, engine
    from sqlalchemy import desc
    ret = {'message':""}
    session = Session()
    nine_id1 = int(dic["nine_id"])
    user2 = session.query(User).filter(User.username==dic['username']).first()
    if user2 == None:
        ret['message'] = "user is not found"
        return ret
    nine_id2 = user2.nine_id
    if nine_id1 == nine_id2:
        ret['message'] = "you can't add yourself as your friend"
        return ret
    friend = session.query(Friend).filter(((Friend.nine_id1==nine_id1)&(Friend.nine_id2==nine_id2)|(Friend.nine_id2==nine_id1)&(Friend.nine_id1==nine_id2))).order_by(desc(Friend.time)).first()
    if friend != None:
        ret['message'] = "you are already friend"
        return ret
    new_friend = Friend(nine_id1=nine_id1,nine_id2=nine_id2)
    session.add(new_friend)
    session.commit()
    ret['message'] = ""
    session.close()
    return ret

def get_friendlist(dic):
    from model import Session, User, Friend, engine
    from sqlalchemy import desc
    session = Session()
    nine_id = int(dic["nine_id"])
    friend_list = session.query(Friend).filter((Friend.nine_id1==nine_id)|(Friend.nine_id2==nine_id)).order_by(desc(Friend.time)).all()
    ret = {
        "friendlist":[]
    }
    for friend in friend_list:
        if friend.nine_id1 == nine_id:
            title=session.query(User).filter(User.nine_id==friend.nine_id2).first().username
        else:
            title=session.query(User).filter(User.nine_id==friend.nine_id1).first().username
        time=datetime.strftime(friend.time, "%Y-%m-%d\n%H:%M:%S")
        A_friend={
            'title':title,
            "time":time
        }
        ret["friendlist"].append(A_friend)
    session.close()
    return ret

def update_chatlist(nine_id):
    dic = {
        "type": "get_chatlist",
        "nine_id": nine_id
    }
    if nine_id in nine_id_to_socket:
        for socket in nine_id_to_socket[nine_id]:
            send_to_client(socket, get_chatlist(dic))

def update_chat(nine_id1,nine_id2,username):
    chat_id = get_chat_id2(nine_id1,nine_id2)
    dic = {
        "type": "get_chat",
        "nine_id": nine_id1,
        "username": username
    }
    if chat_id in chat_id_to_socket:
        for socket in chat_id_to_socket[chat_id]:
            send_to_client(socket, get_chat(dic))

def send_message(dic):
    from model import Session, User, Chat, Latest_Chat, engine
    from sqlalchemy import desc
    session = Session()
    nine_id1 = int(dic["nine_id"])
    nine_id2 = session.query(User).filter(User.username==dic['username']).first().nine_id
    new_message = Chat(nine_id1=nine_id1, nine_id2=nine_id2,
                    message=dic["message"], type=1)
    session.add(new_message)
    session.commit()
    latest_chatlist = session.query(Latest_Chat).filter(((Latest_Chat.nine_id1==nine_id1)&(Latest_Chat.nine_id2==nine_id2))|((Latest_Chat.nine_id1==nine_id2)&(Latest_Chat.nine_id2==nine_id1))).order_by(desc(Latest_Chat.time)).all()
    for latest_chat in latest_chatlist:
        session.delete(latest_chat)
    session.commit()
    new_latest_message = Latest_Chat(nine_id1=new_message.nine_id1, nine_id2=new_message.nine_id2,message=new_message.message, type=1)
    session.add(new_latest_message)
    session.commit()
    username = session.query(User).filter(User.nine_id==nine_id1).first().username
    update_chat(nine_id1,nine_id2,dic['username'])
    update_chat(nine_id2,nine_id1,username)
    update_chatlist(nine_id1)
    update_chatlist(nine_id2)
    session.close()

def send_image(dic):
    from model import Session, User, Chat, Latest_Chat, engine
    from sqlalchemy import desc
    session = Session()
    nine_id1 = int(dic["nine_id"])
    username = session.query(User).filter(User.nine_id==dic['nine_id']).first().username
    nine_id2 = session.query(User).filter(User.username==dic['username']).first().nine_id
    import base64
    import io
    image = io.BytesIO(base64.b64decode(dic['str_image']))
    from PIL import Image
    image = Image.open(image)
    path = imagedir+'/image'+str(session.query(Chat).count())+'.'+dic['format']
    image.save(path)

    new_message = Chat(nine_id1=nine_id1, nine_id2=nine_id2,message=path, type=2)
    session.add(new_message)
    session.commit()
    latest_chatlist = session.query(Latest_Chat).filter(((Latest_Chat.nine_id1==nine_id1)&(Latest_Chat.nine_id2==nine_id2))|((Latest_Chat.nine_id1==nine_id2)&(Latest_Chat.nine_id2==nine_id1))).order_by(desc(Latest_Chat.time)).all()
    for latest_chat in latest_chatlist:
        session.delete(latest_chat)
    session.commit()
    new_latest_message = Latest_Chat(nine_id1=new_message.nine_id1, nine_id2=new_message.nine_id2,message=username+" send a picture", type=1)
    session.add(new_latest_message)
    session.commit()
    username = session.query(User).filter(User.nine_id==nine_id1).first().username
    update_chat(nine_id1,nine_id2,dic['username'])
    update_chat(nine_id2,nine_id1,username)
    update_chatlist(nine_id1)
    update_chatlist(nine_id2)
    session.close()

def get_chat(dic):
    from model import Session, User, Chat, engine
    from sqlalchemy import desc
    session = Session()
    nine_id1 = int(dic["nine_id"])
    nine_id2=session.query(User).filter(User.username==dic['username']).first().nine_id
    record_list = session.query(Chat).filter(((Chat.nine_id1==nine_id1)&(Chat.nine_id2==nine_id2)|(Chat.nine_id2==nine_id1)&(Chat.nine_id1==nine_id2))).order_by(Chat.time).all()

    ret = {
        'title':dic['username'],
        "record_list":[]
    }
    for record in record_list:
        direction=None
        message = None
        type = None
        format = "None"
        if record.nine_id1==nine_id1:
            direction="to"
        else:
            direction="from"

        if record.type == 1:
            message=record.message
            type=1
            
        if record.type == 2:
            import base64
            with open(record.message, "rb") as image:
                message = base64.b64encode(image.read()).decode('utf-8')
            type=2
            import imghdr
            format = imghdr.what(record.message)

        time=datetime.strftime(record.time, "%Y-%m-%d %H:%M:%S")
        A_message={
            "direction":direction,
            "message":message,
            "time":time,
            "type":type,
            "format":format
        }
        ret["record_list"].append(A_message)
    session.close()
    return ret

def get_chatlist(dic):
    from model import Session, User, Latest_Chat, engine
    from sqlalchemy import desc
    session = Session()
    nine_id = int(dic["nine_id"])
    latest_chatlist = session.query(Latest_Chat).filter((Latest_Chat.nine_id1==nine_id)|(Latest_Chat.nine_id2==nine_id)).order_by(desc(Latest_Chat.time)).all()
    ret = {
        "chatlist":[]
    }
    for latest_chat in latest_chatlist:
        if latest_chat.nine_id1 == nine_id:
            title=session.query(User).filter(User.nine_id==latest_chat.nine_id2).first().username
        else:
            title=session.query(User).filter(User.nine_id==latest_chat.nine_id1).first().username
        message=latest_chat.message
        time=datetime.strftime(latest_chat.time, "%Y-%m-%d\n%H:%M:%S")
        A_chat={
            'title':title,
            "message":message,
            "time":time
        }
        ret["chatlist"].append(A_chat)
    session.close()
    return ret
    
def login(dic):
    account_type = 'e-mail address'
    if valid_email(dic["account"]):
        account_type = 'username'
    nine_id = login_user(dic["account"],dic["password"],account_type)
    dic = {
        'message':"",
        'nine_id':-1
    }
    if nine_id == -1:
        dic['message'] = "The " + account_type + " and/or password you specified are not correct."
    else:
        dic['message'] = "login success!"
        dic["nine_id"] = nine_id
    return dic

def add_user(dic):
    from model import Session, User, engine
    session = Session()
    err_msg = check_user(dic["username"],dic["email"],dic["password"],dic["confirm_password"])
    ret = {
        'message':""
    }
    if err_msg != None:
        ret['message'] = err_msg
        return ret

    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(dic["password"].encode('utf-8'), salt)
    friend_code=generate_friend_code()
    new_user = User(username=dic["username"], password=hashed,
                    email=dic["email"], friend_code=friend_code)
    session.add(new_user)
    session.commit()
    ret['message'] = "signup success!"
    session.close()
    return ret

def get_chat_id2(nine_id1,nine_id2):
    return nine_id1 * 1000000 + nine_id2

def get_chat_id(nine_id1,username):
    from model import Session, User, engine
    session = Session()
    nine_id2 = session.query(User).filter(User.username==username).first().nine_id
    session.close()
    return nine_id1 * 1000000 + nine_id2

def keep_track_chat(client_socket, nine_id):
    while True:
        try:
            clientMessage = str(client_socket.recv(1000000), encoding='utf-8')
        except socket.error as e:
            print(e)
            break
        clientMessage = clientMessage.replace("'", "\"")
        print('rcv',clientMessage)
        dic = transform_to_dic(clientMessage)
        if dic["type"] == 'get_chat':
            serverMessage = get_chat(dic)
            send_to_client(client_socket, serverMessage)
        if dic["type"] == 'send_message':
            send_message(dic)
        elif dic["type"] == 'send_image':
            send_image(dic)
        elif dic["type"] == 'leave_chat':
            client_socket.close()
            break
    print('close thread '+str(threading.get_ident()))
    chat_id = get_chat_id(nine_id, dic["username"])
    chat_id_to_socket[chat_id].remove(client_socket)

def keep_track_chatlist(client_socket, nine_id):
    while True:
        try:
            clientMessage = str(client_socket.recv(1000000), encoding='utf-8')
        except socket.error as e:
            print(e)
            break
        clientMessage = clientMessage.replace("'", "\"")
        print('rcv',clientMessage)
        dic = transform_to_dic(clientMessage)
        if dic["type"] == 'get_chatlist':
            serverMessage = get_chatlist(dic)
            send_to_client(client_socket, serverMessage)
        elif dic["type"] == 'leave_chatlist':
            client_socket.close()
            break
    print('close thread '+str(threading.get_ident()))
    nine_id_to_socket[nine_id].remove(client_socket)

def cleanup_function():
    for chat_id in chat_id_to_socket:
        for client_socket in chat_id_to_socket[chat_id]:
            client_socket.close()
    
    for thread in all_thread:
        thread.join()
    
    print('success clean up')

def server_method(client_socket,dic):
    serverMessage = ''
    if dic["type"] == 'signup':
        serverMessage = add_user(dic)
    elif dic["type"] == 'login':
        serverMessage = login(dic)
    elif dic["type"] == 'get_friendlist':
        serverMessage = get_friendlist(dic)
    elif dic["type"] == 'add_friend':
        serverMessage = add_friend(dic)
    else:
        nine_id = int(dic["nine_id"])
        if dic["type"] == 'keep_track_chat':
            chat_id = get_chat_id(nine_id, dic["username"])
            if chat_id not in chat_id_to_socket:
                chat_id_to_socket[chat_id] = []
            chat_id_to_socket[chat_id].append(client_socket)
            send_to_client(client_socket, {'message':"ok"})
            thread = threading.Thread(target = keep_track_chat, args = (client_socket,nine_id,))
            thread.setDaemon(True)
            all_thread.append(thread)
            thread.start()
            
        if dic["type"] == 'keep_track_chatlist':
            if nine_id not in nine_id_to_socket:
                nine_id_to_socket[nine_id] = []
            nine_id_to_socket[nine_id].append(client_socket)
            send_to_client(client_socket, {'message':"ok"})
            thread = threading.Thread(target = keep_track_chatlist, args = (client_socket,nine_id,))
            thread.setDaemon(True)
            all_thread.append(thread)
            thread.start()
        return
    send_to_client(client_socket, serverMessage)
    client_socket.close()

def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    return s.getsockname()[0]

def transform_to_dic(clientMessage):
    dic = json.loads(clientMessage)
    for key in dic:
        if isinstance(dic[key], str):
            dic[key] = dic[key].replace("~!@#$%^&*()~!@#$%^&*(~!@#$%^&*", "'")
            dic[key] = dic[key].replace(')(*&^%$#@!)(*&^%$#@!(*&^%$#@!~', '"')
        if isinstance(dic[key], list):
            for dic2 in dic[key]:
                for key2 in dic2:
                    if isinstance(dic2[key2], str):
                        dic2[key2] = dic2[key2].replace("~!@#$%^&*()~!@#$%^&*(~!@#$%^&*", "'")
                        dic2[key2] = dic2[key2].replace(')(*&^%$#@!)(*&^%$#@!(*&^%$#@!~', '"')
    return dic

def create_server():
    # HOST = get_ip_address()
    HOST = "127.0.0.1"
    PORT = 8000
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(30)
    flag = False
    print('server is start at ' + str(HOST) + ':' + str(PORT))

    while True:    
        client_socket, addr = server.accept()
        clientMessage = str(client_socket.recv(1000000), encoding='utf-8')
        print('Client message is:', clientMessage)
        clientMessage = clientMessage.replace("'", "\"")
        print('rcv',clientMessage)
        dic = transform_to_dic(clientMessage)
        server_method(client_socket,dic)
    

if __name__ == "__main__":
    if not os.path.isdir(imagedir):
        os.mkdir(imagedir)
    atexit.register(cleanup_function)
    create_server()