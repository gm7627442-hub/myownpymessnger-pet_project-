import sqlite3
from datetime import datetime

def view_database():
    conn = sqlite3.connect('messenger.db')
    cursor = conn.cursor()
    
    print("=" * 50)
    print("ПРОСМОТР БАЗЫ ДАННЫХ MESSENGER")
    print("=" * 50)
    
    # Показываем таблицы
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"\nНайдено таблиц: {len(tables)}")
    
    for table in tables:
        table_name = table[0]
        print(f"\n{'='*30}")
        print(f"ТАБЛИЦА: {table_name}")
        print(f"{'='*30}")
        
        # Показываем структуру таблицы
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        print("Структура:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        # Показываем данные
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"Записей: {count}")
        
        if count > 0:
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            
            # Показываем первые 10 записей
            for i, row in enumerate(rows[:10]):
                print(f"  {i+1}. {row}")
            
            if count > 10:
                print(f"  ... и еще {count - 10} записей")
    
    # Детальная информация о пользователях
    print(f"\n{'='*50}")
    print("ДЕТАЛЬНАЯ ИНФОРМАЦИЯ О ПОЛЬЗОВАТЕЛЯХ")
    print(f"{'='*50}")
    
    cursor.execute('''
        SELECT u.id, u.username, u.created_at, 
               COUNT(m.id) as message_count
        FROM users u
        LEFT JOIN messages m ON u.id = m.user_id
        GROUP BY u.id
        ORDER BY u.created_at
    ''')
    
    users = cursor.fetchall()
    for user in users:
        user_id, username, created_at, msg_count = user
        print(f"ID: {user_id}, Имя: {username}, Сообщений: {msg_count}, Зарегистрирован: {created_at}")
    
    # Последние сообщения
    print(f"\n{'='*50}")
    print("ПОСЛЕДНИЕ 10 СООБЩЕНИЙ")
    print(f"{'='*50}")
    
    cursor.execute('''
        SELECT m.id, u.username, r.name, m.content, m.created_at
        FROM messages m
        JOIN users u ON m.user_id = u.id
        JOIN rooms r ON m.room_id = r.id
        ORDER BY m.created_at DESC
        LIMIT 10
    ''')
    
    messages = cursor.fetchall()
    for msg in messages:
        msg_id, username, room, content, created_at = msg
        print(f"[{created_at}] {username} в '{room}': {content}")
    
    conn.close()

if __name__ == "__main__":
    view_database()