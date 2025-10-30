import socket
import threading
import sys

class TestAuthClient:
    def __init__(self, host='localhost', port=5555):
        self.host = host
        self.port = port
        self.socket = None
        self.running = False
    
    def connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            print(f"Подключились к {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"Ошибка подключения: {e}")
            return False
    
    def receive_messages(self):
        while self.running:
            try:
                data = self.socket.recv(1024).decode('utf-8')
                if data:
                    print(f"\n{data}")
                    print("> ", end="", flush=True)
                else:
                    break
            except:
                break
    
    def start(self):
        if not self.connect():
            return
        
        self.running = True
        receiver = threading.Thread(target=self.receive_messages)
        receiver.daemon = True
        receiver.start()
        
        try:
            while self.running:
                message = input("> ")
                if message.lower() == '/exit':
                    self.running = False
                    break
                self.socket.send(message.encode('utf-8'))
        except KeyboardInterrupt:
            print("\nВыход...")
        finally:
            self.running = False
            if self.socket:
                self.socket.close()

if __name__ == "__main__":
    client = TestAuthClient()
    client.start()