import socket
import json

def connect_to_server(HOST, PORT):
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((HOST, PORT))
        return client
    except socket.timeout:
        return None
    except socket.error:
        return None

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

def send_dict_to_server(client, dic):
    for key in dic:
        if isinstance(dic[key], str):
            print(dic[key])
            dic[key] = dic[key].replace("'", "~!@#$%^&*()~!@#$%^&*(~!@#$%^&*")
            dic[key] = dic[key].replace('"', ')(*&^%$#@!)(*&^%$#@!(*&^%$#@!~')
    dic = str(dic)
    dic = dic.replace("'", "\"")
    print("client send: ",dic)
    json_msg = json.loads(dic)
    client.sendall(str(json_msg).encode())
    
def rcv_dict_from_server(client):
    serverMessage = client.recv(1000000).decode('utf-8')
    print('rcv server: ', serverMessage)
    client.close()
    serverMessage = serverMessage.replace("'", "\"")
    dic = transform_to_dic(serverMessage)
    return dic

def keep_rcv_dict_from_server(client):
    serverMessage = client.recv(1000000).decode('utf-8')
    print('rcv server: ', serverMessage)
    serverMessage = serverMessage.replace("'", "\"")
    dic = transform_to_dic(serverMessage)
    return dic