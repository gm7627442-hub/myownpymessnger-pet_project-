import socket
import threading
import sys

class ChatClient:
    def __init__(self, host='localhost', port=5555):
        self.host = host
        self.port = port
        self.socket = None
        self.nickname = "User"
    
    def connect(self, nickname=None):
        if nickname:
            self.nickname = nickname
            
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            print(f"Подключились к серверу {self.host}:{self.port}")
            
            data = self.socket.recv(1024).decode('utf-8')
            if data == "NICK":
                self.socket.send(self.nickname.encode('utf-8'))
                print(f"Ваш ник: {self.nickname}")
            
            return True
            
        except Exception as e:
            print(f"Ошибка подключения: {e}")
            return False
    
    def send_message(self, message):
        if not self.socket:
            print("Не подключены к серверу")
            return False
            
        try:
            self.socket.send(message.encode('utf-8'))
            return True
        except Exception as e:
            print(f"Ошибка отправки: {e}")
            return False
    
    def receive_messages(self):
        while True:
            try:
                message = self.socket.recv(1024).decode('utf-8')
                if message:
                    print(f"\n{message}")
                    print("> ", end="", flush=True)
                else:
                    break
            except:
                break
    
    def start_chat(self):
        if not self.connect():
            return
            
        receive_thread = threading.Thread(target=self.receive_messages)
        receive_thread.daemon = True
        receive_thread.start()
        
        print("Чат запущен. Команды: /online, /time, /nick <name>, /exit")
        
        try:
            while True:
                message = input("> ")
                
                if message == "/exit":
                    break
                else:
                    self.send_message(message)
                    
        except KeyboardInterrupt:
            print("Выход из чата")
        finally:
            if self.socket:
                self.socket.close()

if __name__ == "__main__":
    nickname = input("Введите ваш ник: ") or "User"
    client = ChatClient()
    client.nickname = nickname
    client.start_chat()