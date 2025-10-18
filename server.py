import socket
import threading
import time
import json
import sys

class ChatServer:
    def __init__(self, host='localhost', port=5555):
        self.host = host
        self.port = port
        self.clients = {}
        self.lock = threading.Lock()
    
    def start_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(10)
            print(f"Сервер запущен на {self.host}:{self.port}")
            print("Ожидание подключений...")
            
            while True:
                client_socket, address = self.server_socket.accept()
                print(f"Новое подключение: {address}")
                
                client_socket.send("NICK".encode('utf-8'))
                nickname = client_socket.recv(1024).decode('utf-8')
                
                with self.lock:
                    self.clients[client_socket] = nickname
                
                print(f"Пользователь '{nickname}' присоединился")
                self.broadcast(f"{nickname} присоединился к чату", client_socket)
                
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, nickname)
                )
                client_thread.daemon = True
                client_thread.start()
                
        except Exception as e:
            print(f"Ошибка сервера: {e}")
        finally:
            self.stop_server()
    
    def handle_client(self, client_socket, nickname):
        try:
            while True:
                raw_data = client_socket.recv(1024).decode('utf-8')
                
                if not raw_data:
                    break
                
                print(f"Получено от {nickname}: {raw_data}")
                
                # Обрабатываем как обычный текст (без JSON)
                if raw_data.startswith('/'):
                    self.handle_command(client_socket, nickname, raw_data)
                else:
                    if raw_data.strip():
                        formatted_message = f"{nickname}: {raw_data}"
                        print(f"Сообщение: {formatted_message}")
                        self.broadcast(formatted_message, client_socket)
                    
        except Exception as e:
            print(f"Ошибка с клиентом {nickname}: {e}")
        finally:
            self.remove_client(client_socket, nickname)
    
    def handle_command(self, client_socket, nickname, command):
        command = command.strip()
        
        if command == "/online":
            with self.lock:
                online_users = list(self.clients.values())
            response = f"Онлайн ({len(online_users)}): {', '.join(online_users)}"
            client_socket.send(response.encode('utf-8'))
            
        elif command == "/time":
            current_time = time.strftime("%H:%M:%S")
            response = f"Время сервера: {current_time}"
            client_socket.send(response.encode('utf-8'))
            
        elif command.startswith("/nick "):
            new_nick = command[6:].strip()
            if new_nick:
                with self.lock:
                    self.clients[client_socket] = new_nick
                old_nick = nickname
                response = f"Ник изменен с '{old_nick}' на '{new_nick}'"
                client_socket.send(response.encode('utf-8'))
                self.broadcast(f"{old_nick} сменил ник на {new_nick}")
            else:
                client_socket.send("Неверный ник".encode('utf-8'))
                
        else:
            client_socket.send("Неизвестная команда".encode('utf-8'))
    
    def broadcast(self, message, sender_socket=None):
        disconnected_clients = []
        
        with self.lock:
            clients_copy = self.clients.copy()
        
        for client, nickname in clients_copy.items():
            if client != sender_socket:
                try:
                    client.send(message.encode('utf-8'))
                except:
                    disconnected_clients.append((client, nickname))
        
        for client, nickname in disconnected_clients:
            self.remove_client(client, nickname)
    
    def remove_client(self, client_socket, nickname):
        with self.lock:
            if client_socket in self.clients:
                del self.clients[client_socket]
        
        try:
            client_socket.close()
        except:
            pass
        
        print(f"{nickname} покинул чат")
        self.broadcast(f"{nickname} покинул чат")
    
    def stop_server(self):
        print("Остановка сервера...")
        with self.lock:
            for client in self.clients.keys():
                try:
                    client.close()
                except:
                    pass
            self.clients.clear()
        
        if hasattr(self, 'server_socket'):
            self.server_socket.close()
        print("Сервер остановлен")

if __name__ == "__main__":
    server = ChatServer()
    
    try:
        server.start_server()
    except KeyboardInterrupt:
        print("Получен сигнал прерывания")
        server.stop_server()