import sqlite3
import bcrypt
from datetime import datetime

class Database:
    def __init__(self, db_name='messenger.db'):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.create_tables()
    
    def create_tables(self):
        """Создание таблиц пользователей, комнат и сообщений"""
        cursor = self.conn.cursor()
        
        # Таблица пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица комнат
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rooms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users (id)
            )
        ''')
        
        # Таблица сообщений
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                room_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (room_id) REFERENCES rooms (id)
            )
        ''')
       
       # Таблица приватных сообщений
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS private_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_user_id INTEGER NOT NULL,
                to_user_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                is_read BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (from_user_id) REFERENCES users (id),
                FOREIGN KEY (to_user_id) REFERENCES users (id)
            )
        ''')

        
        # Создаем дефолтную комнату
        cursor.execute('''
            INSERT OR IGNORE INTO rooms (name, created_by) 
            VALUES (?, ?)
        ''', ('general', 1))
        
        self.conn.commit()

    def save_private_message(self, from_user_id, to_user_id, content):
        """Сохранение приватного сообщения"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO private_messages (from_user_id, to_user_id, content)
            VALUES (?, ?, ?)
        ''', (from_user_id, to_user_id, content))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_private_messages(self, user_id, other_user_id=None, limit=50):
        """Получение приватных сообщений между пользователями"""
        cursor = self.conn.cursor()
        
        if other_user_id:
            # Сообщения с конкретным пользователем
            cursor.execute('''
                SELECT pm.id, u1.username as from_user, u2.username as to_user, 
                       pm.content, pm.created_at, pm.is_read
                FROM private_messages pm
                JOIN users u1 ON pm.from_user_id = u1.id
                JOIN users u2 ON pm.to_user_id = u2.id
                WHERE (pm.from_user_id = ? AND pm.to_user_id = ?) 
                   OR (pm.from_user_id = ? AND pm.to_user_id = ?)
                ORDER BY pm.created_at ASC
                LIMIT ?
            ''', (user_id, other_user_id, other_user_id, user_id, limit))
        else:
            # Все приватные сообщения пользователя
            cursor.execute('''
                SELECT pm.id, u1.username as from_user, u2.username as to_user, 
                       pm.content, pm.created_at, pm.is_read
                FROM private_messages pm
                JOIN users u1 ON pm.from_user_id = u1.id
                JOIN users u2 ON pm.to_user_id = u2.id
                WHERE pm.from_user_id = ? OR pm.to_user_id = ?
                ORDER BY pm.created_at DESC
                LIMIT ?
            ''', (user_id, user_id, limit))
        
        return cursor.fetchall()
    
    def get_conversation_partners(self, user_id):
        """Получение списка пользователей, с которыми есть приватные сообщения"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT DISTINCT u.id, u.username
            FROM users u
            WHERE u.id IN (
                SELECT from_user_id FROM private_messages WHERE to_user_id = ?
                UNION
                SELECT to_user_id FROM private_messages WHERE from_user_id = ?
            )
        ''', (user_id, user_id))
        return cursor.fetchall()
    
    def mark_messages_as_read(self, user_id, from_user_id):
        """Пометить сообщения как прочитанные"""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE private_messages 
            SET is_read = TRUE 
            WHERE to_user_id = ? AND from_user_id = ? AND is_read = FALSE
        ''', (user_id, from_user_id))
        self.conn.commit()
        return cursor.rowcount
    
    def get_user_by_username(self, username):
        """Получение пользователя по имени"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT id, username FROM users WHERE username = ?', (username,))
        return cursor.fetchone()    
    
    def register_user(self, username, password):
        """Регистрация нового пользователя"""
        try:
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO users (username, password_hash)
                VALUES (?, ?)
            ''', (username, password_hash))
            self.conn.commit()
            return True, "Регистрация успешна"
        except sqlite3.IntegrityError:
            return False, "Пользователь уже существует"
        except Exception as e:
            return False, f"Ошибка регистрации: {str(e)}"
    
    def verify_user(self, username, password):
        """Проверка логина и пароля"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT id, password_hash FROM users WHERE username = ?
        ''', (username,))
        
        result = cursor.fetchone()
        if result and bcrypt.checkpw(password.encode('utf-8'), result[1]):
            return True, result[0]  # user_id
        return False, "Неверный логин или пароль"
    
    def get_user_by_id(self, user_id):
        """Получение пользователя по ID"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT id, username FROM users WHERE id = ?', (user_id,))
        return cursor.fetchone()
    
    def create_room(self, room_name, created_by):
        """Создание новой комнаты"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO rooms (name, created_by)
                VALUES (?, ?)
            ''', (room_name, created_by))
            self.conn.commit()
            return True, "Комната создана"
        except sqlite3.IntegrityError:
            return False, "Комната уже существует"
    
    def get_rooms(self):
        """Получение списка всех комнат"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT r.id, r.name, u.username 
            FROM rooms r 
            LEFT JOIN users u ON r.created_by = u.id
        ''')
        return cursor.fetchall()
    
    def save_message(self, user_id, room_id, content):
        """Сохранение сообщения в базу"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO messages (user_id, room_id, content)
            VALUES (?, ?, ?)
        ''', (user_id, room_id, content))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_message_history(self, room_id, limit=50):
        """Получение истории сообщений комнаты"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT m.id, u.username, m.content, m.created_at
            FROM messages m
            JOIN users u ON m.user_id = u.id
            WHERE m.room_id = ?
            ORDER BY m.created_at DESC
            LIMIT ?
        ''', (room_id, limit))
        return cursor.fetchall()[::-1]  # Переворачиваем чтобы новые были в конце

    def close(self):
        """Закрытие соединения с БД"""
        self.conn.close()