from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.anchorlayout import AnchorLayout
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
import os
from kivy.resources import resource_add_path, resource_find
from kivy.core.window import Window
from kivy.properties import ObjectProperty
from connect import connect_to_server, send_dict_to_server, rcv_dict_from_server, keep_rcv_dict_from_server
from kivy.clock import Clock, mainthread
import atexit
import threading
from kivy.resources import resource_add_path, resource_find

basedir = os.path.abspath(os.path.dirname(__file__))
imagedir = os.path.join(basedir, 'image')
all_thread = []
all_socket = []
ip = "127.0.0.1"
port = 8000


class ChooseIpWindow(Screen):
    ip_input = ObjectProperty(None)
    port_input = ObjectProperty(None)
    inside_grid = ObjectProperty(None)
    error_hint = ObjectProperty(None)
    def __init__(self, **kw):
        super().__init__(**kw)

    def send_call_back(self):
        ip_string = self.ip_input.text
        port_string = self.port_input.text
        valid1 = False
        valid2 = False
        s = ""
        import socket
        try:
            socket.inet_aton(ip_string)
            valid1 = True
        except:
            s += "ip"
        try:
            if 1 <= int(port_string) <= 65535:
                valid2 = True
            else:
                raise ValueError
        except ValueError:
            if valid1:
                s += "port"
            else:
                s += ", port"
        if valid1 and valid2:
            global ip, port
            ip = ip_string
            port = int(port_string)
            loginwindow = self.manager.get_screen("loginwindow")
            loginwindow.hide_error_hint()
            self.manager.current = 'loginwindow'
        else:
            s += " not correct"
            self.show_error_hint(s)

    def show_error_hint(self, msg):
        self.error_hint.text = msg
        self.error_hint.height = 10
        self.error_hint.color = (1, 0, 0, 1)
        self.inside_grid.spacing = 20
        self.inside_grid.height = 75
    
    def hide_error_hint(self):
        self.error_hint.text = ""
        self.error_hint.height = 0
        self.error_hint.color = (1, 1, 1, 1)
        self.inside_grid.spacing = 0
        self.inside_grid.height = 45


class FileChooseWindow(Screen):
    image = ObjectProperty(None)
    error_hint = ObjectProperty(None)
    filechooser = ObjectProperty(None)
    nine_id = 1
    username = ''

    def __init__(self, **kw):
        super().__init__(**kw)
        Window.bind(on_drop_file=self._on_drop_file)

    def selected(self,filename):
        print(filename)
        try:
            self.image.source = filename[0]
        except:
            pass

    def _on_drop_file(self, window, file_path, x, y):
        print(file_path.decode("utf-8") )
        try:
            self.image.source = file_path.decode("utf-8") 
        except:
            pass
        return

    def hide_error_hint(self):
        self.error_hint.text = ''
    
    def show_error_hint(self,msg):
        self.error_hint.text = msg

    def confirm_button(self):
        if self.image.source == '':
            self.show_error_hint("can't be null")
            return
        import imghdr
        try:
            format = imghdr.what(self.image.source)
        except:
            self.show_error_hint("file not exist")
            return
        if format == None:
            self.show_error_hint("the file you choosed is not an image")
            return
        self.hide_error_hint()

        from PIL import Image
        imgFile = Image.open(self.image.source)
        width = 200
        ratio = float(width)/imgFile.size[0]
        height = int(imgFile.size[1]*ratio)
        imgFile = imgFile.resize((width, height), Image.BILINEAR)
        import io
        img_byte_arr = io.BytesIO()
        imgFile.save(img_byte_arr, format=format)

        self.manager.current = 'chatwindow'
        chatwindow = self.manager.get_screen("chatwindow")
        chatwindow.enter_chat(self.nine_id,self.username)
        chatwindow.image_message(img_byte_arr,format)
        Window.clearcolor = (255, 255, 255, 255)
    
    def return_call_back(self):
        self.manager.current = 'chatwindow'
        chatwindow = self.manager.get_screen("chatwindow")
        chatwindow.enter_chat(self.nine_id,self.username)
        Window.clearcolor = (255, 255, 255, 255)

class AddFriendWindow(Screen):
    send_input = ObjectProperty(None)
    error_hint = ObjectProperty(None)
    inside_grid = ObjectProperty(None)
    nine_id = 1

    def return_call_back(self):
        self.manager.current = 'friendlistwindow'
        friendlistwindow = self.manager.get_screen("friendlistwindow")
        friendlistwindow.refresh(self.nine_id)

    def send_call_back(self):
        dic = {
            "type": "add_friend",
            "nine_id": self.nine_id,
            "username": self.send_input.text
        }
        client = connect_to_server(ip, port)
        if client == None:
            self.show_error_hint("server has no respond")
            pass
        else:
            send_dict_to_server(client, dic)
            dic = rcv_dict_from_server(client)
            if dic['message'] == "":
                self.show_error_hint("add friend success")
            else:
                self.show_error_hint(dic['message'])
        self.send_input.text = ""

    def show_error_hint(self, msg):
        self.error_hint.text = msg
        self.error_hint.height = 10
        self.error_hint.color = (1, 0, 0, 1)
        self.inside_grid.spacing = 20
        self.inside_grid.height = 75
    
    def hide_error_hint(self):
        self.error_hint.text = ""
        self.error_hint.height = 0
        self.error_hint.color = (1, 1, 1, 1)
        self.inside_grid.spacing = 0
        self.inside_grid.height = 45

class FriendListWidget(Button):
    title = ObjectProperty(None)
    time = ObjectProperty(None)
    nine_id = 1
    
    def press_call_back(self):
        friend_list_window = self.parent.parent.parent.parent
        friend_list_window.manager.current = 'chatwindow'
        chatwindow = friend_list_window.manager.get_screen("chatwindow")
        chatwindow.enter_chat(self.nine_id,self.title.text)

class FriendListWindow(Screen):
    scroll_grid = ObjectProperty(None)
    nine_id = 1
    username = 'none'

    def __init__(self, **kwargs):
        super(FriendListWindow, self).__init__(**kwargs)

    def refresh(self, nine_id):
        self.scroll_grid.clear_widgets()
        self.nine_id = nine_id
        dic = {
            "type": "get_friendlist",
            "nine_id": self.nine_id
        }
        client = connect_to_server(ip, port)
        if client == None:
            # self.show_error_hint("server has no respond!")
            pass
        else:
            send_dict_to_server(client, dic)
            friendlist = rcv_dict_from_server(client)
            self.scroll_grid.height =  70 * len(friendlist["friendlist"])
            for friend in friendlist["friendlist"]:
                button = FriendListWidget()
                button.nine_id = self.nine_id
                self.scroll_grid.add_widget(button)
                button.title.text = friend["title"]
                button.time.text = friend["time"]

    def chat_button(self):
        self.manager.current = 'chatlistwindow'
        chatlistwindow = self.manager.get_screen("chatlistwindow")
        chatlistwindow.enter_chatlist(self.nine_id)
    
    def add_friend_button(self):
        self.manager.current = 'addfriendwindow'
        addfriendwindow = self.manager.get_screen("addfriendwindow")
        addfriendwindow.nine_id = self.nine_id
        addfriendwindow.hide_error_hint()

class WindowManager(ScreenManager):
    pass

class Image_from(AnchorLayout):
    pass

class Image_to(AnchorLayout):
    pass

class Message_from(AnchorLayout):
    pass

class Message_to(AnchorLayout):
    pass

class Time(Label):
    pass

class ChatWindow(Screen):
    scroll_grid = ObjectProperty(None)
    send_input = ObjectProperty(None)
    scroll = ObjectProperty(None)
    image = ObjectProperty(None)
    image_layout = ObjectProperty(None)
    cancel_button = ObjectProperty(None)
    cancel_button_image = ObjectProperty(None)
    socket = None
    imageFile = None
    format = None
    flag = False
    nine_id = 1
    username = 'none'

    def __init__(self, **kwargs):
        super(ChatWindow, self).__init__(**kwargs)

    def return_call_back(self):
        self.leave_chat()
        self.manager.current = 'chatlistwindow'
        chatlistwindow = self.manager.get_screen("chatlistwindow")
        chatlistwindow.enter_chatlist(self.nine_id)
        
    @mainthread
    def send_call_back(self):
        if self.send_input.text != "":
            dic = {
                "type": "send_message",
                "nine_id": self.nine_id,
                "username": self.username,
                "message": self.send_input.text
            }
            send_dict_to_server(self.socket, dic)
            self.send_input.text = ""
            self.send_input.focus = True

        if self.image_layout.height != 0:
            byte_image = self.imageFile.getvalue()
            import base64
            str_image = base64.b64encode(byte_image).decode('utf8')
            dic = {
                "type": "send_image",
                "nine_id": self.nine_id,
                "username": self.username,
                "str_image": str_image,
                "format": self.format
            }
            send_dict_to_server(self.socket, dic)
            self.cancel_button_call_back()
    
    def image_call_back(self):
        self.leave_chat()
        self.manager.current = 'filechoosewindow'
        filechoosewindow = self.manager.get_screen("filechoosewindow")
        filechoosewindow.image.source=""
        filechoosewindow.hide_error_hint()
        filechoosewindow.nine_id=self.nine_id
        filechoosewindow.username=self.username
        Window.clearcolor = (0, 0, 0, 255)
        
    
    def keep_track(self):
        dic = {
            "type": "keep_track_chat",
            "nine_id": self.nine_id,
            "username": self.username
        }
        send_dict_to_server(self.socket, dic)
        keep_rcv_dict_from_server(self.socket)
        self.request()
        print(id(self.socket))
        while self.flag:
            dic = keep_rcv_dict_from_server(self.socket)
            self.refresh(dic)
            
    def leave_chat(self):
        dic = {
            "type": "leave_chat",
            "nine_id": self.nine_id,
            "username": self.username
        }
        print(id(self.socket))
        send_dict_to_server(self.socket, dic)
        self.socket.close()
        all_socket.remove(self.socket)
        self.flag = False

    def enter_chat(self, nine_id, username):
        self.flag = True
        self.nine_id = nine_id
        self.username = username
        self.socket = connect_to_server(ip, port)
        print(id(self.socket))
        thread = threading.Thread(target = self.keep_track)
        thread.setDaemon(True)
        all_thread.append(thread)
        all_socket.append(self.socket)
        thread.start()
    
    @mainthread
    def refresh(self,dic):
        self.scroll_grid.clear_widgets()
        record_list = dic["record_list"]
        for record in record_list:
            time = Time()
            time.text=record["time"]
            self.scroll_grid.add_widget(time)
            message = None
            if record["type"] == 1:
                if record["direction"] == 'to':
                    message = Message_to()
                else:        
                    message = Message_from()
                message.message_label.text = record["message"]
                self.scroll_grid.add_widget(message)
                self.scroll_grid.do_layout()
                message.message_label.texture_update()
            if record["type"] == 2:
                if record["direction"] == 'to':
                    image = Image_to()
                else:        
                    image = Image_from()
                import base64
                import io
                from kivy.core.image import Image as CoreImage
                from io import BytesIO
                data = io.BytesIO(base64.b64decode(record["message"]))
                data.seek(0)
                rcv_image = CoreImage(BytesIO(data.read()), ext=record["format"])
                image.message_image.texture = rcv_image.texture
                self.scroll_grid.add_widget(image)

            Clock.schedule_once(self.resizing_scroll,0.2)

    def request(self):
        dic = {
            "type": "get_chat",
            "nine_id": self.nine_id,
            "username": self.username
        }
        print(id(self.socket))
        send_dict_to_server(self.socket, dic)
        
    def resizing_scroll(self,*largs):
        self.scroll.scroll_y = 0

    def image_message(self,data,format):
        from kivy.core.image import Image as CoreImage
        from io import BytesIO

        data.seek(0)
        self.imageFile = data
        image = CoreImage(BytesIO(data.read()), ext=format)
        self.format = format
        self.image.texture = image.texture
        self.image.size = 50,50
        self.cancel_button.size = 50,50
        self.cancel_button_image.size = 30,30
        self.image_layout.height = 50
    
    def cancel_button_call_back(self):
        self.image.size = 0,0
        self.cancel_button.size = 0,0
        self.cancel_button_image.size = 0,0
        self.image_layout.height = 0

class ChatListWidget(Button):
    title = ObjectProperty(None)
    message = ObjectProperty(None)
    time = ObjectProperty(None)
    nine_id = 1
    
    def press_call_back(self):
        chat_list_window = self.parent.parent.parent.parent
        chat_list_window.leave_chatlist()
        chat_list_window.manager.current = 'chatwindow'
        chatwindow = chat_list_window.manager.get_screen("chatwindow")
        chatwindow.enter_chat(self.nine_id,self.title.text)

class ChatListWindow(Screen):
    scroll_grid = ObjectProperty(None)
    nine_id = 1
    socket = None
    flag = False

    def __init__(self, **kwargs):
        super(ChatListWindow, self).__init__(**kwargs)

    def leave_chatlist(self):
        dic = {
            "type": "leave_chatlist",
            "nine_id": self.nine_id
        }
        print(id(self.socket))
        send_dict_to_server(self.socket, dic)
        self.socket.close()
        all_socket.remove(self.socket)
        self.flag = False

    def keep_track(self):
        dic = {
            "type": "keep_track_chatlist",
            "nine_id": self.nine_id,
        }
        send_dict_to_server(self.socket, dic)
        keep_rcv_dict_from_server(self.socket)
        self.request()
        print(id(self.socket))
        while self.flag:
            dic = keep_rcv_dict_from_server(self.socket)
            self.refresh(dic)

    def enter_chatlist(self, nine_id):
        self.flag = True
        self.nine_id = nine_id
        self.socket = connect_to_server(ip, port)
        print(id(self.socket))
        thread = threading.Thread(target = self.keep_track)
        thread.setDaemon(True)
        all_thread.append(thread)
        all_socket.append(self.socket)
        thread.start()

    def request(self):
        self.nine_id = self.nine_id
        dic = {
            "type": "get_chatlist",
            "nine_id": self.nine_id
        }
        send_dict_to_server(self.socket, dic)

    @mainthread
    def refresh(self, dic):
        self.scroll_grid.clear_widgets()
        chatlist = dic["chatlist"]
        for chat in chatlist:
            button = ChatListWidget()
            button.nine_id = self.nine_id
            self.scroll_grid.add_widget(button)
            button.title.text = chat["title"]
            button.message.text = chat["message"]
            button.time.text = chat["time"]

    def friend_button(self):
        self.leave_chatlist()
        self.manager.current = 'friendlistwindow'
        friendlistwindow = self.manager.get_screen("friendlistwindow")
        friendlistwindow.refresh(self.nine_id)

class LoginWindow(Screen):
    account = ObjectProperty(None)
    password = ObjectProperty(None)
    error_hint = ObjectProperty(None)
    inside_grid = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(LoginWindow, self).__init__(**kwargs)

    def login_call_back(self):
        dic = {
            "type": "login",
            "account": self.account.text,
            "password": self.password.text
        }
        client = connect_to_server(ip, port)
        if client == None:
            self.show_error_hint("server has no respond!")
        else:
            send_dict_to_server(client, dic)
            dic = rcv_dict_from_server(client)
            if dic['nine_id'] != -1:
                self.show_error_hint("signup success!")
                nine_id = dic['nine_id']
                self.manager.current = 'chatlistwindow'
                chatlistwindow = self.manager.get_screen("chatlistwindow")
                chatlistwindow.enter_chatlist(nine_id)
            else:
                self.show_error_hint(dic['message'])
        self.account.text = ""
        self.password.text = ""
    
    def enter_call_back(self):
        dic = {
            "type": "login",
            "account": self.account.text,
            "password": self.password.text
        }
        client = connect_to_server(ip, port)
        if client == None:
            self.show_error_hint("server has no respond!")
        else:
            send_dict_to_server(client, dic)
            dic = rcv_dict_from_server(client)
            if dic['nine_id'] != -1:
                self.show_error_hint("signup success!")
                nine_id = dic['nine_id']
                self.manager.current = 'chatlistwindow'
                chatlistwindow = self.manager.get_screen("chatlistwindow")
                chatlistwindow.enter_chatlist(nine_id)
            else:
                self.show_error_hint(dic['message'])

    def choose_ip_call_back(self):
        chooseipwindow = self.manager.get_screen("chooseipwindow")
        chooseipwindow.hide_error_hint()
        self.manager.current = 'chooseipwindow'

    def signup_call_back(self):
        signupwindow = self.manager.get_screen("signupwindow")
        signupwindow.hide_error_hint()
        self.manager.current = 'signupwindow'

    def show_error_hint(self, msg):
        self.error_hint.text = msg
        self.error_hint.height = 10
        self.error_hint.color = (1, 0, 0, 1)
        self.inside_grid.spacing = 20
        self.inside_grid.height = 75

    def hide_error_hint(self):
        self.error_hint.text = ""
        self.error_hint.height = 0
        self.error_hint.color = (1, 1, 1, 1)
        self.inside_grid.spacing = 0
        self.inside_grid.height = 45

class SignupWindow(Screen):
    username = ObjectProperty(None)
    password = ObjectProperty(None)
    confirm_password = ObjectProperty(None)
    email = ObjectProperty(None)
    error_hint = ObjectProperty(None)
    inside_grid = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(SignupWindow, self).__init__(**kwargs)
    
    def return_call_back(self):
        loginwindow = self.manager.get_screen("loginwindow")
        loginwindow.hide_error_hint()
        self.manager.current = 'loginwindow'

    def signup_call_back(self):
        dic = {
            "type": "signup",
            "username": self.username.text,
            "password": self.password.text,
            "confirm_password": self.confirm_password.text,
            "email": self.email.text
        }
        client = connect_to_server(ip, port)
        if client == None:
            self.show_error_hint("server has no respond!")
        else:
            send_dict_to_server(client, dic)
            dic = rcv_dict_from_server(client)
            self.show_error_hint(dic['message'])
            if dic['message'] == "signup success!":
                loginwindow = self.manager.get_screen("loginwindow")
                loginwindow.hide_error_hint()
                self.manager.current = 'loginwindow'
        self.username.text = ""
        self.password.text = ""
        self.confirm_password.text = ""
        self.email.text = ""
    
    def enter_call_back(self):
        dic = {
            "type": "signup",
            "username": self.username.text,
            "password": self.password.text,
            "confirm_password": self.confirm_password.text,
            "email": self.email.text
        }
        client = connect_to_server(ip, port)
        if client == None:
            self.show_error_hint("server has no respond!")
        else:
            send_dict_to_server(client, dic)
            dic = rcv_dict_from_server(client)
            self.show_error_hint(dic['message'])
            if dic['message'] == "signup success!":
                loginwindow = self.manager.get_screen("loginwindow")
                loginwindow.hide_error_hint()
                self.manager.current = 'loginwindow'

    def show_error_hint(self, msg):
        self.error_hint.text = msg
        self.error_hint.height = 10
        self.error_hint.color = (1, 0, 0, 1)
        self.inside_grid.spacing = 20
        self.inside_grid.height = 75

    def hide_error_hint(self):
        self.error_hint.text = ""
        self.error_hint.height = 0
        self.error_hint.color = (1, 1, 1, 1)
        self.inside_grid.spacing = 0
        self.inside_grid.height = 45

class NineApp(App):
    def build(self):
        return WindowManager()

def cleanup_function():
    for socket in all_socket:
        socket.close()

    for thread in all_thread:
        print('cleaning')
        thread.join()
    
    print('success clean up')

if __name__ == "__main__":
    from kivy.config import Config
    atexit.register(cleanup_function)
    Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
    Window.clearcolor = (255, 255, 255, 255)
    NineApp().run()
