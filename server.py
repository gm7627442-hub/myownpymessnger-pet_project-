import socket
import threading
import time
from database import Database

class AuthChatServer:
    def __init__(self, host='localhost', port=5555):
        self.host = host
        self.port = port
        self.db = Database()
        self.clients = {}  # {socket: {'user_id': int, 'username': str, 'current_room': int}}
        self.rooms = {'general': 1}  # {room_name: room_id}
        self.lock = threading.Lock()
        
        # Загружаем комнаты из БД
        self.load_rooms()
    
    def load_rooms(self):
        """Загрузка комнат из базы данных"""
        rooms_data = self.db.get_rooms()
        for room_id, room_name, _ in rooms_data:
            self.rooms[room_name] = room_id
    
    def start_server(self):
        """Запуск сервера"""
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
                
                # Создаем поток для аутентификации и обработки клиента
                client_thread = threading.Thread(
                    target=self.handle_client_auth,
                    args=(client_socket,)
                )
                client_thread.daemon = True
                client_thread.start()
                
        except Exception as e:
            print(f"Ошибка сервера: {e}")
        finally:
            self.stop_server()
    
    def handle_client_auth(self, client_socket):
        """Обработка аутентификации клиента"""
        try:
            authenticated = False
            user_id = None
            username = None
            
            while not authenticated:
                # Отправляем меню аутентификации
                auth_menu = (
                    "Добро пожаловать! Выберите действие:\n"
                    "1. /login <username> <password>\n"
                    "2. /register <username> <password>\n"
                    "3. /exit"
                )
                client_socket.send(auth_menu.encode('utf-8'))
                
                data = client_socket.recv(1024).decode('utf-8').strip()
                
                if data.startswith('/login '):
                    # Обработка входа
                    parts = data.split(' ', 2)
                    if len(parts) == 3:
                        _, username, password = parts
                        success, result = self.db.verify_user(username, password)
                        if success:
                            authenticated = True
                            user_id = result
                            client_socket.send("Успешный вход!".encode('utf-8'))
                        else:
                            client_socket.send(f"Ошибка: {result}".encode('utf-8'))
                    else:
                        client_socket.send("Неверный формат: /login username password".encode('utf-8'))
                
                elif data.startswith('/register '):
                    # Обработка регистрации
                    parts = data.split(' ', 2)
                    if len(parts) == 3:
                        _, username, password = parts
                        success, message = self.db.register_user(username, password)
                        if success:
                            client_socket.send("Регистрация успешна! Теперь войдите.".encode('utf-8'))
                        else:
                            client_socket.send(f"Ошибка: {message}".encode('utf-8'))
                    else:
                        client_socket.send("Неверный формат: /register username password".encode('utf-8'))
                
                elif data == '/exit':
                    client_socket.close()
                    return
                
                else:
                    client_socket.send("Неизвестная команда".encode('utf-8'))
            
            # После успешной аутентификации
            if authenticated and user_id:
                with self.lock:
                    self.clients[client_socket] = {
                        'user_id': user_id,
                        'username': username,
                        'current_room': 1  # general room
                    }
                
                print(f"Пользователь '{username}' аутентифицирован")
                self.broadcast_system(f"Пользователь {username} присоединился к чату")
                
                # Отправляем историю сообщений
                self.send_message_history(client_socket, 1)
                
                # Переходим к основному циклу обработки сообщений
                self.handle_client_messages(client_socket, user_id, username)
                
        except Exception as e:
            print(f"Ошибка аутентификации: {e}")
        finally:
            self.remove_client(client_socket)
    
    def handle_client_messages(self, client_socket, user_id, username):
        """Обработка сообщений аутентифицированного клиента"""
        try:
            help_text = (
                "\nДоступные команды:\n"
                "/rooms - список комнат\n"
                "/join <room> - присоединиться к комнате\n"
                "/create <room> - создать комнату\n"
                "/users - список пользователей онлайн\n"
                "/myinfo - ваша информация\n"
                "/help - справка по командам\n"
                "/exit - выход\n"
            )
            client_socket.send(help_text.encode('utf-8'))
            
            while True:
                data = client_socket.recv(1024).decode('utf-8').strip()
                
                if not data:
                    break
                
                if data.startswith('/'):
                    # Обработка команд
                    self.handle_command(client_socket, user_id, username, data)
                else:
                    # Обычное сообщение
                    self.handle_normal_message(client_socket, user_id, username, data)
                    
        except Exception as e:
            print(f"Ошибка обработки сообщений: {e}")
        finally:
            self.remove_client(client_socket)
    
    def handle_command(self, client_socket, user_id, username, command):
        """Обработка специальных команд"""
        parts = command.split(' ')
        cmd = parts[0]
        
        if cmd == '/rooms':
            # Показать список комнат
            rooms_list = "Доступные комнаты:\n"
            for room_name, room_id in self.rooms.items():
                rooms_list += f"- {room_name}\n"
            client_socket.send(rooms_list.encode('utf-8'))
        
        elif cmd == '/join' and len(parts) > 1:
            # Присоединиться к комнате
            room_name = parts[1]
            if room_name in self.rooms:
                with self.lock:
                    self.clients[client_socket]['current_room'] = self.rooms[room_name]
                client_socket.send(f"Вы присоединились к комнате {room_name}".encode('utf-8'))
                self.send_message_history(client_socket, self.rooms[room_name])
            else:
                client_socket.send(f"Комната {room_name} не найдена".encode('utf-8'))
        
        elif cmd == '/create' and len(parts) > 1:
            # Создать комнату
            room_name = parts[1]
            success, message = self.db.create_room(room_name, user_id)
            if success:
                self.load_rooms()  # Обновляем список комнат
                client_socket.send(f"Комната {room_name} создана".encode('utf-8'))
            else:
                client_socket.send(f"Ошибка: {message}".encode('utf-8'))
        
        elif cmd == '/users':
            # Показать онлайн пользователей
            online_users = "Пользователи онлайн:\n"
            with self.lock:
                for client_data in self.clients.values():
                    online_users += f"- {client_data['username']}\n"
            client_socket.send(online_users.encode('utf-8'))
        
        elif cmd == '/debug_db' and username == 'admin':  # Только для админа
            # Информация о БД
            rooms_count = len(self.rooms)
            users_count = len(self.clients)
            
            cursor = self.db.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            total_users = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM messages")
            total_messages = cursor.fetchone()[0]
            
            info = (
                f"Информация о базе данных:\n"
                f"Пользователей в базе: {total_users}\n"
                f"Пользователей онлайн: {users_count}\n"
                f"Комнат: {rooms_count}\n"
                f"Всего сообщений: {total_messages}\n"
            )
            client_socket.send(info.encode('utf-8'))
        
        elif cmd == '/myinfo':
            # Информация о текущем пользователе
            with self.lock:
                current_room_id = self.clients[client_socket]['current_room']
            
            # Находим имя текущей комнаты
            current_room_name = "general"
            for room_name, room_id in self.rooms.items():
                if room_id == current_room_id:
                    current_room_name = room_name
                    break
            
            info = (
                f"Ваша информация:\n"
                f"Имя: {username}\n"
                f"ID: {user_id}\n"
                f"Текущая комната: {current_room_name}\n"
            )
            client_socket.send(info.encode('utf-8'))
        
        elif cmd == '/help':
            # Справка по командам
            help_text = (
                "Доступные команды:\n"
                "/rooms - список комнат\n"
                "/join <room> - присоединиться к комнате\n"
                "/create <room> - создать комнату\n"
                "/users - список пользователей онлайн\n"
                "/myinfo - ваша информация\n"
                "/help - эта справка\n"
                "/exit - выход\n"
            )
            client_socket.send(help_text.encode('utf-8'))
        
        elif cmd == '/exit':
            client_socket.send("До свидания!".encode('utf-8'))
            raise Exception("Выход по команде")
        
        else:
            client_socket.send("Неизвестная команда".encode('utf-8'))
    
    def handle_normal_message(self, client_socket, user_id, username, message):
        """Обработка обычного сообщения"""
        if not message.strip():
            return
            
        with self.lock:
            current_room = self.clients[client_socket]['current_room']
        
        # Сохраняем сообщение в БД
        message_id = self.db.save_message(user_id, current_room, message)
        
        # Форматируем и рассылаем
        formatted_message = f"{username}: {message}"
        print(f"Сообщение в комнате {current_room}: {formatted_message}")
        
        # Рассылаем всем в текущей комнате отправителя
        self.broadcast_to_room(formatted_message, current_room, client_socket)
    
    def send_message_history(self, client_socket, room_id):
        """Отправка истории сообщений комнаты"""
        history = self.db.get_message_history(room_id, 20)
        if history:
            client_socket.send("История сообщений:\n".encode('utf-8'))
            for msg_id, msg_username, content, timestamp in history:
                time_str = timestamp.split(' ')[1][:5]  # Берем только время
                client_socket.send(f"[{time_str}] {msg_username}: {content}\n".encode('utf-8'))
    
    def broadcast_to_room(self, message, room_id, sender_socket=None):
        """Рассылка сообщения всем в указанной комнате"""
        disconnected_clients = []
        
        with self.lock:
            clients_copy = self.clients.copy()
        
        for client, client_data in clients_copy.items():
            if client != sender_socket and client_data['current_room'] == room_id:
                try:
                    client.send(message.encode('utf-8'))
                except:
                    disconnected_clients.append(client)
        
        # Удаляем отключившихся клиентов
        for client in disconnected_clients:
            self.remove_client(client)
    
    def broadcast_system(self, message):
        """Системное сообщение для всех"""
        disconnected_clients = []
        
        with self.lock:
            clients_copy = self.clients.copy()
        
        for client in clients_copy.keys():
            try:
                client.send(f"[СИСТЕМА] {message}".encode('utf-8'))
            except:
                disconnected_clients.append(client)
        
        for client in disconnected_clients:
            self.remove_client(client)
    
    def remove_client(self, client_socket):
        """Удаление клиента"""
        username = None
        with self.lock:
            if client_socket in self.clients:
                username = self.clients[client_socket]['username']
                del self.clients[client_socket]
        
        try:
            client_socket.close()
        except:
            pass
        
        if username:
            print(f"{username} отключился")
            self.broadcast_system(f"Пользователь {username} покинул чат")
    
    def stop_server(self):
        """Остановка сервера"""
        print("Остановка сервера...")
        self.broadcast_system("Сервер останавливается")
        
        with self.lock:
            for client in self.clients.keys():
                try:
                    client.close()
                except:
                    pass
            self.clients.clear()
        
        self.db.close()
        
        if hasattr(self, 'server_socket'):
            self.server_socket.close()
        print("Сервер остановлен")

if __name__ == "__main__":
    server = AuthChatServer()
    
    try:
        server.start_server()
    except KeyboardInterrupt:
        print("Получен сигнал прерывания")
        server.stop_server()