import socket
import threading
import time
from database import Database
from validation import Validator

class AuthChatServer:
    def __init__(self, host='localhost', port=5555):
        self.host = host
        self.port = port
        self.db = Database()
        self.validator = Validator()
        self.clients = {}
        self.username_to_socket = {}
        self.rooms = {'general': 1}
        self.lock = threading.Lock()
        self.user_message_history = {}
        
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
                auth_menu = (
                    "Добро пожаловать! Выберите действие:\n"
                    "1. /login <username> <password>\n"
                    "2. /register <username> <password>\n"
                    "3. /exit"
                )
                client_socket.send(auth_menu.encode('utf-8'))
                
                data = client_socket.recv(1024).decode('utf-8').strip()
                
                if data.startswith('/login '):
                    parts = data.split(' ', 2)
                    if len(parts) == 3:
                        _, username, password = parts
                        
                        username = self.validator.sanitize_input(username)
                        password = self.validator.sanitize_input(password)
                        
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
                    parts = data.split(' ', 2)
                    if len(parts) == 3:
                        _, username, password = parts
                        
                        username = self.validator.sanitize_input(username)
                        password = self.validator.sanitize_input(password)
                        
                        valid_username, msg_user = self.validator.validate_username(username)
                        if not valid_username:
                            client_socket.send(f"Ошибка имени пользователя: {msg_user}".encode('utf-8'))
                            continue
                        
                        valid_password, msg_pass = self.validator.validate_password(password)
                        if not valid_password:
                            client_socket.send(f"Ошибка пароля: {msg_pass}".encode('utf-8'))
                            continue
                        
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
            
            if authenticated and user_id:
                with self.lock:
                    self.clients[client_socket] = {
                        'user_id': user_id,
                        'username': username,
                        'current_room': 1
                    }
                    self.username_to_socket[username] = client_socket
                    self.user_message_history[user_id] = []
                
                print(f"Пользователь '{username}' аутентифицирован")
                self.broadcast_system(f"Пользователь {username} присоединился к чату")
                
                self.send_message_history(client_socket, 1)
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
                "/msg <user> <message> - приватное сообщение\n"
                "/pm <user> <message> - приватное сообщение (алиас)\n"
                "/inbox - входящие сообщения\n"
                "/chat <user> - начать чат с пользователем\n"
                "/myinfo - ваша информация\n"
                "/help - справка по командам\n"
                "/exit - выход\n"
            )
            client_socket.send(help_text.encode('utf-8'))
            
            while True:
                data = client_socket.recv(1024).decode('utf-8').strip()
                
                if not data:
                    break
                
                data = self.validator.sanitize_input(data)
                
                if data.startswith('/'):
                    self.handle_command(client_socket, user_id, username, data)
                else:
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
            rooms_list = "Доступные комнаты:\n"
            for room_name, room_id in self.rooms.items():
                rooms_list += f"- {room_name}\n"
            client_socket.send(rooms_list.encode('utf-8'))
        
        elif cmd == '/join' and len(parts) > 1:
            room_name = parts[1]
            if room_name in self.rooms:
                with self.lock:
                    self.clients[client_socket]['current_room'] = self.rooms[room_name]
                client_socket.send(f"Вы присоединились к комнате {room_name}".encode('utf-8'))
                self.send_message_history(client_socket, self.rooms[room_name])
            else:
                client_socket.send(f"Комната {room_name} не найдена".encode('utf-8'))
        
        elif cmd == '/create' and len(parts) > 1:
            room_name = parts[1]
            
            valid_room, msg = self.validator.validate_room_name(room_name)
            if not valid_room:
                client_socket.send(f"Ошибка: {msg}".encode('utf-8'))
                return
            
            success, message = self.db.create_room(room_name, user_id)
            if success:
                self.load_rooms()
                client_socket.send(f"Комната {room_name} создана".encode('utf-8'))
            else:
                client_socket.send(f"Ошибка: {message}".encode('utf-8'))
        
        elif cmd == '/users':
            online_users = "Пользователи онлайн:\n"
            with self.lock:
                for client_data in self.clients.values():
                    online_users += f"- {client_data['username']}\n"
            client_socket.send(online_users.encode('utf-8'))
        
        elif cmd == '/get_rooms':
            # Отправляем список комнат в формате для GUI
            rooms_list = "Доступные комнаты:\n"
            for room_name, room_id in self.rooms.items():
                rooms_list += f"- {room_name}\n"
            client_socket.send(rooms_list.encode('utf-8'))    
        
        elif cmd in ['/msg', '/pm'] and len(parts) >= 3:
            target_username = parts[1]
            message = ' '.join(parts[2:])
            
            valid_msg, msg_text = self.validator.validate_message(message)
            if not valid_msg:
                client_socket.send(f"Ошибка: {msg_text}".encode('utf-8'))
                return
            
            if target_username == username:
                client_socket.send("Нельзя отправить сообщение самому себе".encode('utf-8'))
                return
            
            spam_detected, spam_reason = self.validator.detect_spam_patterns(
                message, user_id, self.user_message_history.get(user_id, [])
            )
            if spam_detected:
                client_socket.send(f"Сообщение отклонено: {spam_reason}".encode('utf-8'))
                return
            
            target_socket = None
            with self.lock:
                target_socket = self.username_to_socket.get(target_username)
            
            if target_socket and target_socket in self.clients:
                target_user_id = self.clients[target_socket]['user_id']
                
                self.db.save_private_message(user_id, target_user_id, message)
                
                self._update_message_history(user_id, message)
                
                private_msg = f"[ЛС от {username}] {message}"
                target_socket.send(private_msg.encode('utf-8'))
                
                confirmation = f"[ЛС для {target_username}] {message}"
                client_socket.send(confirmation.encode('utf-8'))
                
                self.db.mark_messages_as_read(target_user_id, user_id)
            else:
                client_socket.send(f"Пользователь {target_username} не в сети".encode('utf-8'))
        
        elif cmd == '/inbox':
            messages = self.db.get_private_messages(user_id, limit=10)
            if not messages:
                client_socket.send("Нет входящих сообщений".encode('utf-8'))
            else:
                inbox = "Последние сообщения:\n"
                for msg_id, from_user, to_user, content, timestamp, is_read in messages:
                    status = "✓" if is_read else "✗"
                    time_str = timestamp.split(' ')[1][:5]
                    direction = "→" if from_user == username else "←"
                    other_user = to_user if from_user == username else from_user
                    inbox += f"[{time_str}] {status} {direction} {other_user}: {content}\n"
                client_socket.send(inbox.encode('utf-8'))
        
        elif cmd == '/chat' and len(parts) > 1:
            target_username = parts[1]
            target_user = self.db.get_user_by_username(target_username)
            if not target_user:
                client_socket.send(f"Пользователь {target_username} не найден".encode('utf-8'))
                return
            
            target_user_id, _ = target_user
            messages = self.db.get_private_messages(user_id, target_user_id, limit=20)
            
            if not messages:
                client_socket.send(f"Нет сообщений с {target_username}".encode('utf-8'))
            else:
                history = f"История чата с {target_username}:\n"
                for msg_id, from_user, to_user, content, timestamp, is_read in messages:
                    time_str = timestamp.split(' ')[1][:5]
                    arrow = "→" if from_user == username else "←"
                    history += f"[{time_str}] {arrow} {content}\n"
                client_socket.send(history.encode('utf-8'))
                self.db.mark_messages_as_read(user_id, target_user_id)
        
        elif cmd == '/debug_db' and username == 'admin':
            rooms_count = len(self.rooms)
            users_count = len(self.clients)
            
            cursor = self.db.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            total_users = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM messages")
            total_messages = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM private_messages")
            total_private = cursor.fetchone()[0]
            
            info = (
                f"Информация о базе данных:\n"
                f"Пользователей в базе: {total_users}\n"
                f"Пользователей онлайн: {users_count}\n"
                f"Комнат: {rooms_count}\n"
                f"Сообщений в чатах: {total_messages}\n"
                f"Приватных сообщений: {total_private}\n"
            )
            client_socket.send(info.encode('utf-8'))
        
        elif cmd == '/myinfo':
            with self.lock:
                current_room_id = self.clients[client_socket]['current_room']
            
            current_room_name = "general"
            for room_name, room_id in self.rooms.items():
                if room_id == current_room_id:
                    current_room_name = room_name
                    break
            
            cursor = self.db.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM messages WHERE user_id = ?", (user_id,))
            public_msgs = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM private_messages WHERE from_user_id = ?", (user_id,))
            sent_private = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM private_messages WHERE to_user_id = ?", (user_id,))
            received_private = cursor.fetchone()[0]
            
            info = (
                f"Ваша информация:\n"
                f"Имя: {username}\n"
                f"ID: {user_id}\n"
                f"Текущая комната: {current_room_name}\n"
                f"Статистика:\n"
                f"  - Сообщений в чатах: {public_msgs}\n"
                f"  - Отправлено ЛС: {sent_private}\n"
                f"  - Получено ЛС: {received_private}\n"
            )
            client_socket.send(info.encode('utf-8'))
        
        elif cmd == '/help':
            help_text = (
                "Доступные команды:\n"
                "/rooms - список комнат\n"
                "/join <room> - присоединиться к комнате\n"
                "/create <room> - создать комнату\n"
                "/users - список пользователей онлайн\n"
                "/msg <user> <message> - приватное сообщение\n"
                "/pm <user> <message> - приватное сообщение (алиас)\n"
                "/inbox - входящие сообщения\n"
                "/chat <user> - начать чат с пользователем\n"
                "/myinfo - ваша информация\n"
                "/help - эта справка\n"
                "/exit - выход\n"
            )
            client_socket.send(help_text.encode('utf-8'))
        
        elif cmd == '/exit':
            client_socket.send("До свидания!".encode('utf-8'))
            raise Exception("Выход по команде")

        elif cmd == '/admin_stats':
            # Расширенная статистика для админа
            if username == 'admin':
                cursor = self.db.conn.cursor()
                
                # Статистика по комнатам
                cursor.execute('''
                    SELECT r.name, COUNT(m.id) as message_count 
                    FROM rooms r 
                    LEFT JOIN messages m ON r.id = m.room_id 
                    GROUP BY r.id
                ''')
                room_stats = cursor.fetchall()
                
                # Активные пользователи
                cursor.execute('''
                    SELECT u.username, COUNT(m.id) as message_count,
                        MAX(m.created_at) as last_active
                    FROM users u 
                    LEFT JOIN messages m ON u.id = m.user_id 
                    GROUP BY u.id 
                    ORDER BY message_count DESC 
                    LIMIT 10
                ''')
                user_stats = cursor.fetchall()
                
                stats = "=== РАСШИРЕННАЯ СТАТИСТИКА ===\n\n"
                stats += "📊 Статистика по комнатам:\n"
                for room_name, count in room_stats:
                    stats += f"  {room_name}: {count} сообщений\n"
                
                stats += "\n👥 Активные пользователи:\n"
                for user, count, last_active in user_stats:
                    stats += f"  {user}: {count} сообщений (активен: {last_active})\n"
                
                client_socket.send(stats.encode('utf-8'))
            else:
                client_socket.send("❌ Недостаточно прав".encode('utf-8'))

        elif cmd == '/admin_broadcast' and username == 'admin':
            # Рассылка системного сообщения всем пользователям
            if len(parts) > 1:
                message = ' '.join(parts[1:])
                self.broadcast_system(f"📢 АДМИНИСТРАТОР: {message}")
                client_socket.send("✅ Системное сообщение отправлено".encode('utf-8'))
            else:
                client_socket.send("❌ Использование: /admin_broadcast <сообщение>".encode('utf-8'))

        elif cmd == '/admin_kick' and username == 'admin' and len(parts) > 1:
            # Отключение пользователя
            target_username = parts[1]
            target_socket = None
            
            with self.lock:
                for sock, data in self.clients.items():
                    if data['username'] == target_username:
                        target_socket = sock
                        break
            
            if target_socket:
                try:
                    target_socket.send("🔒 Вы были отключены администратором".encode('utf-8'))
                    self.remove_client(target_socket)
                    client_socket.send(f"✅ Пользователь {target_username} отключен".encode('utf-8'))
                except:
                    client_socket.send(f"❌ Ошибка при отключении пользователя".encode('utf-8'))

        else:
            client_socket.send("Неизвестная команда".encode('utf-8'))
            # Добавьте эти команды после существующих:



    def handle_normal_message(self, client_socket, user_id, username, message):
        """Обработка обычного сообщения"""
        valid_msg, msg_text = self.validator.validate_message(message)
        if not valid_msg:
            client_socket.send(f"Ошибка: {msg_text}".encode('utf-8'))
            return
        
        spam_detected, spam_reason = self.validator.detect_spam_patterns(
            message, user_id, self.user_message_history.get(user_id, [])
        )
        if spam_detected:
            client_socket.send(f"Сообщение отклонено: {spam_reason}".encode('utf-8'))
            return
        
        with self.lock:
            current_room = self.clients[client_socket]['current_room']
        
        message_id = self.db.save_message(user_id, current_room, message)
        
        self._update_message_history(user_id, message)
        
        formatted_message = f"{username}: {message}"
        print(f"Сообщение в комнате {current_room}: {formatted_message}")
        
        self.broadcast_to_room(formatted_message, current_room, client_socket)
    
    def _update_message_history(self, user_id, message):
        """Обновление истории сообщений пользователя"""
        if user_id not in self.user_message_history:
            self.user_message_history[user_id] = []
        
        self.user_message_history[user_id].append({
            'timestamp': time.time(),
            'message': message
        })
        
        if len(self.user_message_history[user_id]) > 100:
            self.user_message_history[user_id] = self.user_message_history[user_id][-50:]
    
    def send_message_history(self, client_socket, room_id):
        """Отправка истории сообщений комнаты"""
        history = self.db.get_message_history(room_id, 20)
        if history:
            client_socket.send("История сообщений:\n".encode('utf-8'))
            for msg_id, msg_username, content, timestamp in history:
                time_str = timestamp.split(' ')[1][:5]
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
        user_id = None
        
        with self.lock:
            if client_socket in self.clients:
                username = self.clients[client_socket]['username']
                user_id = self.clients[client_socket]['user_id']
                del self.clients[client_socket]
                if username in self.username_to_socket:
                    del self.username_to_socket[username]
        
        if user_id and user_id in self.user_message_history:
            del self.user_message_history[user_id]
        
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
            self.username_to_socket.clear()
        
        self.user_message_history.clear()
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