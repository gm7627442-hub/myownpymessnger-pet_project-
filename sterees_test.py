import socket
import threading
import time

def client_thread(client_id):
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('localhost', 5555))
        
        try:
            nick_request = client.recv(1024).decode('utf-8')
            if nick_request == "NICK":
                client.send(f"User{client_id}".encode('utf-8'))
        except:
            pass
        
        # Отправляем несколько сообщений
        for i in range(10):
            message = f"Сообщение {i} от User{client_id}"
            client.send(message.encode('utf-8'))
            time.sleep(1)
        
        client.close()
        print(f" Клиент {client_id} завершил работу")
        
    except Exception as e:
        print(f" Ошибка в клиенте {client_id}: {e}")

# Запускаем несколько клиентов
threads = []
for i in range(5):  # 5 клиентов
    thread = threading.Thread(target=client_thread, args=(i,))
    threads.append(thread)
    thread.start()
    time.sleep(0.1)  # Небольшая задержка между подключениями

# Ждем завершения всех потоков
for thread in threads:
    thread.join()

print(" Все тесты завершены")