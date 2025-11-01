import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import socket
import threading
import json
import time

class ChatClientGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Мессенджер")
        self.root.geometry("800x600")
        self.root.configure(bg='#2b2b2b')
        
        # Переменные
        self.socket = None
        self.connected = False
        self.username = None
        self.user_id = None
        self.current_room = "general"
        
        # Создаем интерфейс
        self.create_login_frame()
        self.create_chat_frame()
        
        # Показываем окно логина
        self.show_login()
        
    def create_login_frame(self):
        """Создание фрейма авторизации"""
        self.login_frame = tk.Frame(self.root, bg='#2b2b2b')
        
        # Заголовок
        title_label = tk.Label(
            self.login_frame,
            text="Мессенджер",
            font=('Arial', 24, 'bold'),
            fg='white',
            bg='#2b2b2b'
        )
        title_label.pack(pady=20)
        
        # Поля ввода
        input_frame = tk.Frame(self.login_frame, bg='#2b2b2b')
        input_frame.pack(pady=20)
        
        # Имя пользователя
        tk.Label(
            input_frame,
            text="Имя пользователя:",
            font=('Arial', 12),
            fg='white',
            bg='#2b2b2b'
        ).grid(row=0, column=0, padx=5, pady=5, sticky='e')
        
        self.username_entry = tk.Entry(
            input_frame,
            font=('Arial', 12),
            width=20
        )
        self.username_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # Пароль
        tk.Label(
            input_frame,
            text="Пароль:",
            font=('Arial', 12),
            fg='white',
            bg='#2b2b2b'
        ).grid(row=1, column=0, padx=5, pady=5, sticky='e')
        
        self.password_entry = tk.Entry(
            input_frame,
            font=('Arial', 12),
            width=20,
            show='*'
        )
        self.password_entry.grid(row=1, column=1, padx=5, pady=5)
        
        # Кнопки
        button_frame = tk.Frame(self.login_frame, bg='#2b2b2b')
        button_frame.pack(pady=20)
        
        self.login_btn = tk.Button(
            button_frame,
            text="Войти",
            font=('Arial', 12, 'bold'),
            bg='#4CAF50',
            fg='white',
            width=10,
            command=self.login
        )
        self.login_btn.pack(side='left', padx=10)
        
        self.register_btn = tk.Button(
            button_frame,
            text="Регистрация",
            font=('Arial', 12),
            bg='#2196F3',
            fg='white',
            width=10,
            command=self.register
        )
        self.register_btn.pack(side='left', padx=10)
        
        # Статус
        self.status_label = tk.Label(
            self.login_frame,
            text="Не подключено",
            font=('Arial', 10),
            fg='red',
            bg='#2b2b2b'
        )
        self.status_label.pack(pady=10)
        
        # Бинд Enter на кнопку входа
        self.root.bind('<Return>', lambda event: self.login())
        
    def create_chat_frame(self):
        """Создание основного фрейма чата"""
        self.chat_frame = tk.Frame(self.root, bg='#2b2b2b')
        
        # Верхняя панель
        top_frame = tk.Frame(self.chat_frame, bg='#2b2b2b')
        top_frame.pack(fill='x', padx=10, pady=5)
        
        # Информация о пользователе
        self.user_info_label = tk.Label(
            top_frame,
            text="Пользователь: Неизвестно | Комната: general",
            font=('Arial', 10),
            fg='white',
            bg='#2b2b2b'
        )
        self.user_info_label.pack(side='left')
        
        # Кнопка выхода
        self.logout_btn = tk.Button(
            top_frame,
            text="Выйти",
            font=('Arial', 10),
            bg='#f44336',
            fg='white',
            command=self.logout
        )
        self.logout_btn.pack(side='right')
        
        # Основное содержимое
        main_frame = tk.Frame(self.chat_frame, bg='#2b2b2b')
        main_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Левая панель (пользователи и комнаты)
        left_frame = tk.Frame(main_frame, bg='#3c3c3c')
        left_frame.pack(side='left', fill='y', padx=(0, 5))
        
        # Список комнат
        tk.Label(
            left_frame,
            text="Комнаты",
            font=('Arial', 11, 'bold'),
            fg='white',
            bg='#3c3c3c'
        ).pack(pady=(5, 0))
        
        self.rooms_listbox = tk.Listbox(
            left_frame,
            width=20,
            height=8,
            bg='#2b2b2b',
            fg='white',
            selectbackground='#4CAF50'
        )
        self.rooms_listbox.pack(fill='x', padx=5, pady=5)
        self.rooms_listbox.bind('<<ListboxSelect>>', self.on_room_select)
        
        # Кнопка обновления комнат
        self.refresh_rooms_btn = tk.Button(
            left_frame,
            text="Обновить комнаты",
            font=('Arial', 9),
            bg='#2196F3',
            fg='white',
            command=self.refresh_rooms
        )
        self.refresh_rooms_btn.pack(fill='x', padx=5, pady=2)
        
        # Создание комнаты
        create_room_frame = tk.Frame(left_frame, bg='#3c3c3c')
        create_room_frame.pack(fill='x', padx=5, pady=5)
        
        self.new_room_entry = tk.Entry(
            create_room_frame,
            font=('Arial', 9),
            width=12
        )
        self.new_room_entry.pack(side='left', fill='x', expand=True)
        
        self.create_room_btn = tk.Button(
            create_room_frame,
            text="+",
            font=('Arial', 9, 'bold'),
            bg='#4CAF50',
            fg='white',
            width=3,
            command=self.create_room
        )
        self.create_room_btn.pack(side='right', padx=(5, 0))
        
        # Список пользователей
        tk.Label(
            left_frame,
            text="Пользователи онлайн",
            font=('Arial', 11, 'bold'),
            fg='white',
            bg='#3c3c3c'
        ).pack(pady=(10, 0))
        
        self.users_listbox = tk.Listbox(
            left_frame,
            width=20,
            height=12,
            bg='#2b2b2b',
            fg='white',
            selectbackground='#2196F3'
        )
        self.users_listbox.pack(fill='both', expand=True, padx=5, pady=5)
        self.users_listbox.bind('<<ListboxSelect>>', self.on_user_select)
        
        # Правая панель (чат)
        right_frame = tk.Frame(main_frame, bg='#2b2b2b')
        right_frame.pack(side='right', fill='both', expand=True)
        
        # Область сообщений
        tk.Label(
            right_frame,
            text="Сообщения",
            font=('Arial', 11, 'bold'),
            fg='white',
            bg='#2b2b2b'
        ).pack(anchor='w')
        
        self.messages_text = scrolledtext.ScrolledText(
            right_frame,
            wrap=tk.WORD,
            width=60,
            height=20,
            bg='#1e1e1e',
            fg='white',
            font=('Arial', 10),
            state='disabled'
        )
        self.messages_text.pack(fill='both', expand=True, pady=5)
        
        # Панель ввода сообщения
        input_frame = tk.Frame(right_frame, bg='#2b2b2b')
        input_frame.pack(fill='x', pady=5)
        
        self.message_entry = tk.Entry(
            input_frame,
            font=('Arial', 12),
            bg='#3c3c3c',
            fg='white'
        )
        self.message_entry.pack(side='left', fill='x', expand=True, padx=(0, 5))
        self.message_entry.bind('<Return>', self.send_message)
        
        self.send_btn = tk.Button(
            input_frame,
            text="Отправить",
            font=('Arial', 12, 'bold'),
            bg='#4CAF50',
            fg='white',
            command=self.send_message
        )
        self.send_btn.pack(side='right')
        
        # Панель команд
        commands_frame = tk.Frame(right_frame, bg='#2b2b2b')
        commands_frame.pack(fill='x', pady=5)
        
        commands = [
            ("/inbox", self.show_inbox),
            ("/myinfo", self.show_myinfo),
            ("/help", self.show_help)
        ]
        
        for text, command in commands:
            btn = tk.Button(
                commands_frame,
                text=text,
                font=('Arial', 9),
                bg='#555555',
                fg='white',
                command=command
            )
            btn.pack(side='left', padx=2)
    
    def show_login(self):
        """Показать окно авторизации"""
        self.chat_frame.pack_forget()
        self.login_frame.pack(fill='both', expand=True)
        self.username_entry.focus()
    
    def show_chat(self):
        """Показать основное окно чата"""
        self.login_frame.pack_forget()
        self.chat_frame.pack(fill='both', expand=True)
        self.message_entry.focus()
    
    def connect_to_server(self):
        """Подключение к серверу"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect(('localhost', 5555))
            self.connected = True
            self.status_label.config(text="Подключено", fg='green')
            
            # Запускаем поток для приема сообщений
            receive_thread = threading.Thread(target=self.receive_messages, daemon=True)
            receive_thread.start()
            
            return True
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось подключиться к серверу: {e}")
            return False
    
    def login(self):
        """Вход в систему"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not username or not password:
            messagebox.showwarning("Ошибка", "Введите имя пользователя и пароль")
            return
        
        if not self.connect_to_server():
            return
        
        # Отправляем команду входа
        command = f"/login {username} {password}"
        self.socket.send(command.encode('utf-8'))
    
    def register(self):
        """Регистрация нового пользователя"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not username or not password:
            messagebox.showwarning("Ошибка", "Введите имя пользователя и пароль")
            return
        
        if len(password) < 6:
            messagebox.showwarning("Ошибка", "Пароль должен быть не менее 6 символов")
            return
        
        if not self.connect_to_server():
            return
        
        # Отправляем команду регистрации
        command = f"/register {username} {password}"
        self.socket.send(command.encode('utf-8'))
    
    def logout(self):
        """Выход из системы"""
        if self.socket:
            try:
                self.socket.send("/exit".encode('utf-8'))
                self.socket.close()
            except:
                pass
        
        self.connected = False
        self.username = None
        self.user_id = None
        self.current_room = "general"
        
        # Очищаем интерфейс
        self.messages_text.config(state='normal')
        self.messages_text.delete(1.0, tk.END)
        self.messages_text.config(state='disabled')
        
        self.rooms_listbox.delete(0, tk.END)
        self.users_listbox.delete(0, tk.END)
        
        self.show_login()
    
    def receive_messages(self):
        """Получение сообщений от сервера"""
        while self.connected:
            try:
                data = self.socket.recv(1024).decode('utf-8')
                if not data:
                    break
                
                # Обрабатываем сообщение в основном потоке
                self.root.after(0, self.process_message, data)
                
            except Exception as e:
                if self.connected:
                    self.root.after(0, lambda: messagebox.showerror("Ошибка", f"Соединение разорвано: {e}"))
                break
        
        if self.connected:
            self.root.after(0, self.logout)
    
    def process_message(self, message):
        """Обработка полученного сообщения"""
        if message == "Успешный вход!":
            self.username = self.username_entry.get().strip()
            self.user_info_label.config(text=f"Пользователь: {self.username} | Комната: {self.current_room}")
            self.show_chat()
            self.refresh_rooms()
            self.refresh_users()
        
        elif message.startswith("Ошибка:"):
            messagebox.showerror("Ошибка", message)
            self.socket.close()
            self.connected = False
            self.status_label.config(text="Не подключено", fg='red')
        
        elif message.startswith("Регистрация успешна!"):
            messagebox.showinfo("Успех", message)
            self.username_entry.delete(0, tk.END)
            self.password_entry.delete(0, tk.END)
            self.socket.close()
            self.connected = False
            self.status_label.config(text="Не подключено", fg='red')
        
        elif message.startswith("Доступные комнаты:"):
            self.update_rooms_list(message)
        
        elif message.startswith("Пользователи онлайн:"):
            self.update_users_list(message)
        
        elif message.startswith("История сообщений:") or message.startswith("История чата с") or message.startswith("Последние сообщения:") or message.startswith("Ваша информация:") or message.startswith("Информация о базе данных:"):
            self.display_system_message(message)
        
        else:
            self.display_message(message)
    
    def display_message(self, message):
        """Отображение сообщения в чате"""
        self.messages_text.config(state='normal')
        
        # Определяем цвет сообщения
        if message.startswith('[ЛС от') or message.startswith('[ЛС для'):
            tag = "private"
            color = "#FF9800"  # оранжевый
        elif message.startswith('[СИСТЕМА]'):
            tag = "system"
            color = "#f44336"  # красный
        else:
            tag = "normal"
            color = "white"
        
        # Создаем тег для цвета
        self.messages_text.tag_config(tag, foreground=color)
        
        # Добавляем сообщение
        self.messages_text.insert(tk.END, message + "\n", tag)
        self.messages_text.see(tk.END)
        self.messages_text.config(state='disabled')
    
    def display_system_message(self, message):
        """Отображение системного сообщения"""
        self.messages_text.config(state='normal')
        self.messages_text.insert(tk.END, "\n" + "="*50 + "\n", "system")
        self.messages_text.insert(tk.END, message + "\n", "system")
        self.messages_text.insert(tk.END, "="*50 + "\n\n", "system")
        self.messages_text.see(tk.END)
        self.messages_text.config(state='disabled')
    
    def update_rooms_list(self, message):
        """Обновление списка комнат"""
        self.rooms_listbox.delete(0, tk.END)
        
        lines = message.split('\n')[1:]  # Пропускаем первую строку "Доступные комнаты:"
        for line in lines:
            if line.startswith('- '):
                room_name = line[2:].strip()
                self.rooms_listbox.insert(tk.END, room_name)
    
    def update_users_list(self, message):
        """Обновление списка пользователей"""
        self.users_listbox.delete(0, tk.END)
        
        lines = message.split('\n')[1:]  # Пропускаем первую строку "Пользователи онлайн:"
        for line in lines:
            if line.startswith('- '):
                username = line[2:].strip()
                if username != self.username:  # Не показываем себя в списке
                    self.users_listbox.insert(tk.END, username)
    
    def send_message(self, event=None):
        """Отправка сообщения"""
        message = self.message_entry.get().strip()
        if not message:
            return
        
        if not self.connected:
            messagebox.showerror("Ошибка", "Нет подключения к серверу")
            return
        
        try:
            self.socket.send(message.encode('utf-8'))
            self.message_entry.delete(0, tk.END)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось отправить сообщение: {e}")
    
    def on_room_select(self, event):
        """Обработка выбора комнаты"""
        selection = self.rooms_listbox.curselection()
        if selection:
            room_name = self.rooms_listbox.get(selection[0])
            if room_name != self.current_room:
                self.socket.send(f"/join {room_name}".encode('utf-8'))
                self.current_room = room_name
                self.user_info_label.config(text=f"Пользователь: {self.username} | Комната: {self.current_room}")
    
    def on_user_select(self, event):
        """Обработка выбора пользователя для приватного сообщения"""
        selection = self.users_listbox.curselection()
        if selection:
            username = self.users_listbox.get(selection[0])
            message = tk.simpledialog.askstring("Приватное сообщение", f"Сообщение для {username}:")
            if message:
                self.socket.send(f"/msg {username} {message}".encode('utf-8'))
    
    def refresh_rooms(self):
        """Обновление списка комнат"""
        if self.connected:
            self.socket.send("/rooms".encode('utf-8'))
    
    def refresh_users(self):
        """Обновление списка пользователей"""
        if self.connected:
            self.socket.send("/users".encode('utf-8'))
    
    def create_room(self):
        """Создание новой комнаты"""
        room_name = self.new_room_entry.get().strip()
        if not room_name:
            messagebox.showwarning("Ошибка", "Введите название комнаты")
            return
        
        if self.connected:
            self.socket.send(f"/create {room_name}".encode('utf-8'))
            self.new_room_entry.delete(0, tk.END)
    
    def show_inbox(self):
        """Показать входящие сообщения"""
        if self.connected:
            self.socket.send("/inbox".encode('utf-8'))
    
    def show_myinfo(self):
        """Показать информацию о пользователе"""
        if self.connected:
            self.socket.send("/myinfo".encode('utf-8'))
    
    def show_help(self):
        """Показать справку"""
        help_text = """
Доступные команды:

В чате:
/rooms - список комнат
/join <room> - присоединиться к комнате  
/create <room> - создать комнату
/users - список пользователей онлайн
/msg <user> <message> - приватное сообщение
/inbox - входящие сообщения
/myinfo - ваша информация
/help - справка
/exit - выход

Горячие клавиши:
Enter - отправить сообщение
Выбор пользователя - отправить приватное сообщение
Выбор комнаты - перейти в комнату
        """
        messagebox.showinfo("Справка", help_text)
    
    def run(self):
        """Запуск приложения"""
        self.root.mainloop()

if __name__ == "__main__":
    client = ChatClientGUI()
    client.run()