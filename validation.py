import re
import html

class Validator:
    @staticmethod
    def validate_username(username):
        """Валидация имени пользователя"""
        if not username or len(username) < 3:
            return False, "Имя пользователя должно быть не менее 3 символов"
        
        if len(username) > 20:
            return False, "Имя пользователя должно быть не более 20 символов"
        
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            return False, "Имя пользователя может содержать только буквы, цифры и _"
        
        forbidden_names = ['admin', 'system', 'server', 'root', 'null', 'undefined']
        if username.lower() in forbidden_names:
            return False, "Это имя пользователя запрещено"
        
        return True, "OK"
    
    @staticmethod
    def validate_password(password):
        """Валидация пароля"""
        if len(password) < 6:
            return False, "Пароль должен быть не менее 6 символов"
        
        if len(password) > 100:
            return False, "Пароль слишком длинный"
        
        return True, "OK"
    
    @staticmethod
    def validate_message(message):
        """Валидация сообщения"""
        if not message or not message.strip():
            return False, "Сообщение не может быть пустым"
        
        if len(message) > 1000:
            return False, "Сообщение слишком длинное (макс. 1000 символов)"
        
        return True, "OK"
    
    @staticmethod
    def validate_room_name(room_name):
        """Валидация названия комнаты"""
        if not room_name or len(room_name) < 2:
            return False, "Название комнаты должно быть не менее 2 символов"
        
        if len(room_name) > 30:
            return False, "Название комнаты должно быть не более 30 символов"
        
        if not re.match(r'^[a-zA-Z0-9_\- ]+$', room_name):
            return False, "Название комнаты может содержать только буквы, цифры, пробелы, _ и -"
        
        forbidden_names = ['general', 'all', 'everyone', 'system']
        if room_name.lower() in forbidden_names:
            return False, "Это название комнаты запрещено"
        
        return True, "OK"
    
    @staticmethod
    def sanitize_input(text):
        """Очистка ввода от потенциально опасных символов"""
        if not text:
            return ""
        
        sanitized = html.escape(text)
        
        sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', sanitized)
        
        return sanitized
    
    @staticmethod
    def detect_spam_patterns(text, user_id, message_history):
        """Обнаружение спам-паттернов"""
        text_lower = text.lower()
        
        if re.search(r'(.)\1{10,}', text):
            return True, "Обнаружены повторяющиеся символы"
        
        if len(text) > 20 and sum(1 for c in text if c.isupper()) / len(text) > 0.8:
            return True, "Слишком много заглавных букв"
        
        if len(message_history) > 10:
            recent_messages = message_history[-10:]
            time_diff = recent_messages[-1]['timestamp'] - recent_messages[0]['timestamp']
            if time_diff < 30:
                return True, "Слишком частые сообщения"
        
        banned_words = ['спам', 'реклама', 'http://', 'https://', 'www.']
        for word in banned_words:
            if word in text_lower:
                return True, f"Обнаружено запрещенное слово: {word}"
        
        return False, "OK"