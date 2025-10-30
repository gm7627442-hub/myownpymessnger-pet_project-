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
        
        # Создаем дефолтную комнату
        cursor.execute('''
            INSERT OR IGNORE INTO rooms (name, created_by) 
            VALUES (?, ?)
        ''', ('general', 1))
        
        self.conn.commit()
    
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