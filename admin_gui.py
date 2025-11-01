import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import socket
import threading
import json
import time
from datetime import datetime

class AdminControlPanel:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Административная панель - Мессенджер")
        self.root.geometry("1000x700")
        self.root.configure(bg='#1e1e1e')
        
        # Переменные
        self.socket = None
        self.connected = False
        self.username = "admin"
        self.server_stats = {}
        
        # Создаем интерфейс
        self.create_login_frame()
        self.create_admin_panel()
        
        # Показываем окно логина
        self.show_login()
        
    def create_login_frame(self):
        """Создание фрейма авторизации для админа"""
        self.login_frame = tk.Frame(self.root, bg='#1e1e1e')
        
        # Заголовок
        title_label = tk.Label(
            self.login_frame,
            text="Административная панель",
            font=('Arial', 20, 'bold'),
            fg='white',
            bg='#1e1e1e'
        )
        title_label.pack(pady=30)
        
        # Поля ввода
        input_frame = tk.Frame(self.login_frame, bg='#1e1e1e')
        input_frame.pack(pady=20)
        
        # Имя пользователя (фиксировано как admin)
        tk.Label(
            input_frame,
            text="Администратор:",
            font=('Arial', 12),
            fg='white',
            bg='#1e1e1e'
        ).grid(row=0, column=0, padx=5, pady=10, sticky='e')
        
        admin_label = tk.Label(
            input_frame,
            text="admin",
            font=('Arial', 12, 'bold'),
            fg='#4CAF50',
            bg='#1e1e1e'
        )
        admin_label.grid(row=0, column=1, padx=5, pady=10, sticky='w')
        
        # Пароль
        tk.Label(
            input_frame,
            text="Пароль:",
            font=('Arial', 12),
            fg='white',
            bg='#1e1e1e'
        ).grid(row=1, column=0, padx=5, pady=10, sticky='e')
        
        self.password_entry = tk.Entry(
            input_frame,
            font=('Arial', 12),
            width=20,
            show='*'
        )
        self.password_entry.grid(row=1, column=1, padx=5, pady=10)
        
        # Кнопки
        button_frame = tk.Frame(self.login_frame, bg='#1e1e1e')
        button_frame.pack(pady=20)
        
        self.login_btn = tk.Button(
            button_frame,
            text="Войти как администратор",
            font=('Arial', 12, 'bold'),
            bg='#4CAF50',
            fg='white',
            width=20,
            command=self.login
        )
        self.login_btn.pack(pady=10)
        
        # Статус
        self.status_label = tk.Label(
            self.login_frame,
            text="Не подключено",
            font=('Arial', 10),
            fg='red',
            bg='#1e1e1e'
        )
        self.status_label.pack(pady=10)
        
        # Бинд Enter на кнопку входа
        self.root.bind('<Return>', lambda event: self.login())
        
    def create_admin_panel(self):
        """Создание основной админ-панели"""
        self.admin_frame = tk.Frame(self.root, bg='#1e1e1e')
        
        # Верхняя панель
        top_frame = tk.Frame(self.admin_frame, bg='#2b2b2b')
        top_frame.pack(fill='x', padx=10, pady=5)
        
        # Информация о сервере
        self.server_info_label = tk.Label(
            top_frame,
            text="Сервер: Не подключено | Время: --:--:--",
            font=('Arial', 10),
            fg='white',
            bg='#2b2b2b'
        )
        self.server_info_label.pack(side='left')
        
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
        
        # Панель быстрых действий
        actions_frame = tk.Frame(self.admin_frame, bg='#1e1e1e')
        actions_frame.pack(fill='x', padx=10, pady=5)
        
        actions = [
            ("📊 Обновить статистику", self.refresh_stats),
            ("👥 Список пользователей", self.refresh_users),
            ("📢 Системное сообщение", self.send_system_message),
            ("🔄 Перезагрузить сервер", self.restart_server),
            ("🚪 Выключить сервер", self.shutdown_server)
        ]
        
        for text, command in actions:
            btn = tk.Button(
                actions_frame,
                text=text,
                font=('Arial', 9),
                bg='#333333',
                fg='white',
                command=command
            )
            btn.pack(side='left', padx=2)
        
        # Создаем вкладки
        self.notebook = ttk.Notebook(self.admin_frame)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Стиль для вкладок
        style = ttk.Style()
        style.configure("TNotebook", background='#1e1e1e')
        style.configure("TNotebook.Tab", background='#333333', foreground='white')
        
        # Вкладка 1: Статистика сервера
        self.stats_tab = tk.Frame(self.notebook, bg='#1e1e1e')
        self.notebook.add(self.stats_tab, text="📊 Статистика")
        
        self.create_stats_tab()
        
        # Вкладка 2: Пользователи
        self.users_tab = tk.Frame(self.notebook, bg='#1e1e1e')
        self.notebook.add(self.users_tab, text="👥 Пользователи")
        
        self.create_users_tab()
        
        # Вкладка 3: Комнаты
        self.rooms_tab = tk.Frame(self.notebook, bg='#1e1e1e')
        self.notebook.add(self.rooms_tab, text="💬 Комнаты")
        
        self.create_rooms_tab()
        
        # Вкладка 4: Мониторинг
        self.monitor_tab = tk.Frame(self.notebook, bg='#1e1e1e')
        self.notebook.add(self.monitor_tab, text="📈 Мониторинг")
        
        self.create_monitor_tab()
        
        # Вкладка 5: Логи
        self.logs_tab = tk.Frame(self.notebook, bg='#1e1e1e')
        self.notebook.add(self.logs_tab, text="📋 Логи")
        
        self.create_logs_tab()
    
    def create_stats_tab(self):
        """Создание вкладки статистики"""
        # Основные метрики
        metrics_frame = tk.Frame(self.stats_tab, bg='#1e1e1e')
        metrics_frame.pack(fill='x', padx=10, pady=10)
        
        self.metrics_text = scrolledtext.ScrolledText(
            metrics_frame,
            wrap=tk.WORD,
            width=80,
            height=15,
            bg='#2b2b2b',
            fg='white',
            font=('Consolas', 10),
            state='disabled'
        )
        self.metrics_text.pack(fill='both', expand=True)
        
        # Кнопки обновления
        button_frame = tk.Frame(self.stats_tab, bg='#1e1e1e')
        button_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Button(
            button_frame,
            text="Обновить статистику БД",
            font=('Arial', 10),
            bg='#2196F3',
            fg='white',
            command=self.refresh_stats
        ).pack(side='left', padx=5)
        
        tk.Button(
            button_frame,
            text="Очистить",
            font=('Arial', 10),
            bg='#ff9800',
            fg='white',
            command=self.clear_stats
        ).pack(side='left', padx=5)
    
    def create_users_tab(self):
        """Создание вкладки управления пользователями"""
        # Список пользователей онлайн
        online_frame = tk.Frame(self.users_tab, bg='#1e1e1e')
        online_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        tk.Label(
            online_frame,
            text="Пользователи онлайн:",
            font=('Arial', 11, 'bold'),
            fg='white',
            bg='#1e1e1e'
        ).pack(anchor='w')
        
        # Фрейм для списка и действий
        list_action_frame = tk.Frame(online_frame, bg='#1e1e1e')
        list_action_frame.pack(fill='both', expand=True, pady=5)
        
        # Список пользователей
        self.users_listbox = tk.Listbox(
            list_action_frame,
            bg='#2b2b2b',
            fg='white',
            selectbackground='#2196F3',
            font=('Arial', 10)
        )
        self.users_listbox.pack(side='left', fill='both', expand=True, padx=(0, 5))
        
        # Панель действий
        action_buttons = tk.Frame(list_action_frame, bg='#1e1e1e')
        action_buttons.pack(side='right', fill='y')
        
        actions = [
            ("🔄 Обновить", self.refresh_users),
            ("📩 Отправить сообщение", self.send_user_message),
            ("🚪 Отключить", self.disconnect_user),
            ("⏰ Заблокировать", self.ban_user),
            ("📊 Статистика пользователя", self.user_stats)
        ]
        
        for text, command in actions:
            btn = tk.Button(
                action_buttons,
                text=text,
                font=('Arial', 9),
                bg='#333333',
                fg='white',
                width=18,
                command=command
            )
            btn.pack(pady=2)
    
    def create_rooms_tab(self):
        """Создание вкладки управления комнатами"""
        rooms_frame = tk.Frame(self.rooms_tab, bg='#1e1e1e')
        rooms_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Список комнат
        tk.Label(
            rooms_frame,
            text="Комнаты чата:",
            font=('Arial', 11, 'bold'),
            fg='white',
            bg='#1e1e1e'
        ).pack(anchor='w')
        
        self.rooms_listbox = tk.Listbox(
            rooms_frame,
            bg='#2b2b2b',
            fg='white',
            selectbackground='#4CAF50',
            font=('Arial', 10)
        )
        self.rooms_listbox.pack(fill='both', expand=True, pady=5)
        
        # Действия с комнатами
        room_actions = tk.Frame(rooms_frame, bg='#1e1e1e')
        room_actions.pack(fill='x')
        
        tk.Button(
            room_actions,
            text="🔄 Обновить комнаты",
            font=('Arial', 9),
            bg='#2196F3',
            fg='white',
            command=self.refresh_rooms
        ).pack(side='left', padx=2)
        
        tk.Button(
            room_actions,
            text="➕ Создать комнату",
            font=('Arial', 9),
            bg='#4CAF50',
            fg='white',
            command=self.create_room
        ).pack(side='left', padx=2)
        
        tk.Button(
            room_actions,
            text="🗑️ Удалить комнату",
            font=('Arial', 9),
            bg='#f44336',
            fg='white',
            command=self.delete_room
        ).pack(side='left', padx=2)
        
        # Создание новой комнаты
        create_frame = tk.Frame(rooms_frame, bg='#1e1e1e')
        create_frame.pack(fill='x', pady=5)
        
        tk.Label(
            create_frame,
            text="Новая комната:",
            font=('Arial', 9),
            fg='white',
            bg='#1e1e1e'
        ).pack(side='left')
        
        self.new_room_entry = tk.Entry(
            create_frame,
            font=('Arial', 9),
            width=20
        )
        self.new_room_entry.pack(side='left', padx=5)
        self.new_room_entry.bind('<Return>', lambda e: self.create_room())
    
    def create_monitor_tab(self):
        """Создание вкладки мониторинга"""
        monitor_frame = tk.Frame(self.monitor_tab, bg='#1e1e1e')
        monitor_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Графики (заглушка - в реальности можно использовать matplotlib)
        tk.Label(
            monitor_frame,
            text="Мониторинг активности сервера",
            font=('Arial', 11, 'bold'),
            fg='white',
            bg='#1e1e1e'
        ).pack(anchor='w')
        
        # Заглушка для графиков
        graph_placeholder = tk.Label(
            monitor_frame,
            text="Графики активности\n(для реализации используйте matplotlib)",
            font=('Arial', 14),
            fg='#666666',
            bg='#2b2b2b',
            width=50,
            height=15
        )
        graph_placeholder.pack(fill='both', expand=True, pady=10)
        
        # Статистика в реальном времени
        stats_frame = tk.Frame(monitor_frame, bg='#1e1e1e')
        stats_frame.pack(fill='x')
        
        self.realtime_stats = tk.Label(
            stats_frame,
            text="Загрузка...",
            font=('Consolas', 9),
            fg='white',
            bg='#1e1e1e',
            justify='left'
        )
        self.realtime_stats.pack(anchor='w')
    
    def create_logs_tab(self):
        """Создание вкладки логов"""
        logs_frame = tk.Frame(self.logs_tab, bg='#1e1e1e')
        logs_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        tk.Label(
            logs_frame,
            text="Логи сервера:",
            font=('Arial', 11, 'bold'),
            fg='white',
            bg='#1e1e1e'
        ).pack(anchor='w')
        
        self.logs_text = scrolledtext.ScrolledText(
            logs_frame,
            wrap=tk.WORD,
            width=80,
            height=20,
            bg='#2b2b2b',
            fg='white',
            font=('Consolas', 9),
            state='disabled'
        )
        self.logs_text.pack(fill='both', expand=True, pady=5)
        
        # Панель управления логами
        log_controls = tk.Frame(logs_frame, bg='#1e1e1e')
        log_controls.pack(fill='x')
        
        tk.Button(
            log_controls,
            text="🔄 Обновить логи",
            font=('Arial', 9),
            bg='#2196F3',
            fg='white',
            command=self.refresh_logs
        ).pack(side='left', padx=2)
        
        tk.Button(
            log_controls,
            text="🗑️ Очистить логи",
            font=('Arial', 9),
            bg='#ff9800',
            fg='white',
            command=self.clear_logs
        ).pack(side='left', padx=2)
        
        tk.Button(
            log_controls,
            text="💾 Сохранить логи",
            font=('Arial', 9),
            bg='#4CAF50',
            fg='white',
            command=self.save_logs
        ).pack(side='left', padx=2)
    
    def show_login(self):
        """Показать окно авторизации"""
        self.admin_frame.pack_forget()
        self.login_frame.pack(fill='both', expand=True)
        self.password_entry.focus()
    
    def show_admin_panel(self):
        """Показать админ-панель"""
        self.login_frame.pack_forget()
        self.admin_frame.pack(fill='both', expand=True)
        self.start_monitoring()
    
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
        """Вход как администратор"""
        password = self.password_entry.get().strip()
        
        if not password:
            messagebox.showwarning("Ошибка", "Введите пароль администратора")
            return
        
        if not self.connect_to_server():
            return
        
        # Отправляем команду входа
        command = f"/login {self.username} {password}"
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
        self.stop_monitoring()
        self.show_login()
    
    def receive_messages(self):
        """Получение сообщений от сервера"""
        while self.connected:
            try:
                data = self.socket.recv(4096).decode('utf-8')
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
            self.show_admin_panel()
            self.refresh_stats()
            self.refresh_users()
            self.refresh_rooms()
        
        elif message.startswith("Ошибка:"):
            messagebox.showerror("Ошибка", message)
            if self.socket:
                self.socket.close()
            self.connected = False
            self.status_label.config(text="Не подключено", fg='red')
        
        elif message.startswith("Информация о базе данных:"):
            self.display_stats(message)
        
        elif message.startswith("Пользователи онлайн:"):
            self.update_users_list(message)
        
        elif message.startswith("Доступные комнаты:"):
            self.update_rooms_list(message)
        
        else:
            self.add_to_logs(message)
    
    def display_stats(self, stats):
        """Отображение статистики"""
        self.metrics_text.config(state='normal')
        self.metrics_text.delete(1.0, tk.END)
        self.metrics_text.insert(tk.END, f"Обновлено: {datetime.now().strftime('%H:%M:%S')}\n\n")
        self.metrics_text.insert(tk.END, stats)
        self.metrics_text.config(state='disabled')
    
    def update_users_list(self, message):
        """Обновление списка пользователей"""
        self.users_listbox.delete(0, tk.END)
        
        lines = message.split('\n')[1:]
        for line in lines:
            if line.startswith('- '):
                username = line[2:].strip()
                if username != self.username:
                    self.users_listbox.insert(tk.END, username)
    
    def update_rooms_list(self, message):
        """Обновление списка комнат"""
        self.rooms_listbox.delete(0, tk.END)
        
        lines = message.split('\n')[1:]
        for line in lines:
            if line.startswith('- '):
                room_name = line[2:].strip()
                self.rooms_listbox.insert(tk.END, room_name)
    
    def add_to_logs(self, message):
        """Добавление сообщения в логи"""
        self.logs_text.config(state='normal')
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.logs_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.logs_text.see(tk.END)
        self.logs_text.config(state='disabled')
    
    def refresh_stats(self):
        """Обновление статистики"""
        if self.connected:
            self.socket.send("/debug_db".encode('utf-8'))
    
    def refresh_users(self):
        """Обновление списка пользователей"""
        if self.connected:
            self.socket.send("/users".encode('utf-8'))
    
    def refresh_rooms(self):
        """Обновление списка комнат"""
        if self.connected:
            self.socket.send("/rooms".encode('utf-8'))
    
    def refresh_logs(self):
        """Обновление логов (заглушка)"""
        self.add_to_logs("--- Обновление логов ---")
    
    def clear_stats(self):
        """Очистка статистики"""
        self.metrics_text.config(state='normal')
        self.metrics_text.delete(1.0, tk.END)
        self.metrics_text.config(state='disabled')
    
    def clear_logs(self):
        """Очистка логов"""
        self.logs_text.config(state='normal')
        self.logs_text.delete(1.0, tk.END)
        self.logs_text.config(state='disabled')
    
    def save_logs(self):
        """Сохранение логов в файл"""
        try:
            filename = f"server_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.logs_text.get(1.0, tk.END))
            messagebox.showinfo("Успех", f"Логи сохранены в файл: {filename}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить логи: {e}")
    
    def send_system_message(self):
        """Отправка системного сообщения"""
        message = tk.simpledialog.askstring("Системное сообщение", "Введите сообщение для всех пользователей:")
        if message and self.connected:
            # Здесь должна быть реализация отправки системного сообщения
            # Пока просто добавим в логи
            self.add_to_logs(f"[СИСТЕМНОЕ СООБЩЕНИЕ] {message}")
    
    def send_user_message(self):
        """Отправка сообщения пользователю"""
        selection = self.users_listbox.curselection()
        if not selection:
            messagebox.showwarning("Ошибка", "Выберите пользователя из списка")
            return
        
        username = self.users_listbox.get(selection[0])
        message = tk.simpledialog.askstring("Сообщение пользователю", f"Сообщение для {username}:")
        if message and self.connected:
            self.socket.send(f"/msg {username} {message}".encode('utf-8'))
    
    def disconnect_user(self):
        """Отключение пользователя"""
        selection = self.users_listbox.curselection()
        if not selection:
            messagebox.showwarning("Ошибка", "Выберите пользователя из списка")
            return
        
        username = self.users_listbox.get(selection[0])
        if messagebox.askyesno("Подтверждение", f"Отключить пользователя {username}?"):
            self.add_to_logs(f"[АДМИН] Отключение пользователя: {username}")
            # Здесь должна быть реализация отключения пользователя
    
    def ban_user(self):
        """Блокировка пользователя"""
        selection = self.users_listbox.curselection()
        if not selection:
            messagebox.showwarning("Ошибка", "Выберите пользователя из списка")
            return
        
        username = self.users_listbox.get(selection[0])
        if messagebox.askyesno("Подтверждение", f"Заблокировать пользователя {username}?"):
            self.add_to_logs(f"[АДМИН] Блокировка пользователя: {username}")
            # Здесь должна быть реализация блокировки пользователя
    
    def user_stats(self):
        """Просмотр статистики пользователя"""
        selection = self.users_listbox.curselection()
        if not selection:
            messagebox.showwarning("Ошибка", "Выберите пользователя из списка")
            return
        
        username = self.users_listbox.get(selection[0])
        messagebox.showinfo("Статистика", f"Статистика пользователя {username}\n\nЭта функция в разработке")
    
    def create_room(self):
        """Создание новой комнаты"""
        room_name = self.new_room_entry.get().strip()
        if not room_name:
            messagebox.showwarning("Ошибка", "Введите название комнаты")
            return
        
        if self.connected:
            self.socket.send(f"/create {room_name}".encode('utf-8'))
            self.new_room_entry.delete(0, tk.END)
    
    def delete_room(self):
        """Удаление комнаты"""
        selection = self.rooms_listbox.curselection()
        if not selection:
            messagebox.showwarning("Ошибка", "Выберите комнату из списка")
            return
        
        room_name = self.rooms_listbox.get(selection[0])
        if room_name == "general":
            messagebox.showwarning("Ошибка", "Нельзя удалить основную комнату 'general'")
            return
        
        if messagebox.askyesno("Подтверждение", f"Удалить комнату '{room_name}'?"):
            self.add_to_logs(f"[АДМИН] Удаление комнаты: {room_name}")
            # Здесь должна быть реализация удаления комнаты
    
    def restart_server(self):
        """Перезагрузка сервера"""
        if messagebox.askyesno("Подтверждение", "Перезагрузить сервер?\nВсе пользователи будут отключены."):
            self.add_to_logs("[АДМИН] Запрос на перезагрузку сервера")
            # Здесь должна быть реализация перезагрузки сервера
    
    def shutdown_server(self):
        """Выключение сервера"""
        if messagebox.askyesno("Подтверждение", "Выключить сервер?\nВсе пользователи будут отключены."):
            self.add_to_logs("[АДМИН] Запрос на выключение сервера")
            # Здесь должна быть реализация выключения сервера
    
    def start_monitoring(self):
        """Запуск мониторинга"""
        self.update_server_info()
    
    def stop_monitoring(self):
        """Остановка мониторинга"""
        if hasattr(self, 'monitor_job'):
            self.root.after_cancel(self.monitor_job)
    
    def update_server_info(self):
        """Обновление информации о сервере"""
        if self.connected:
            current_time = datetime.now().strftime('%H:%M:%S')
            self.server_info_label.config(text=f"Сервер: Подключено | Время: {current_time}")
        
        # Планируем следующее обновление через 1 секунду
        self.monitor_job = self.root.after(1000, self.update_server_info)
    
    def run(self):
        """Запуск приложения"""
        self.root.mainloop()

if __name__ == "__main__":
    admin_panel = AdminControlPanel()
    admin_panel.run()