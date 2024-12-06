import socket
import time

server_address = ("0.0.0.0", 8000)  # IP и порт сервера

# Создание UDP-сокета
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
    # Отправка сообщения серверу
    message = "Привет, сервер!"
    print(f"Отправка: {message}")
    for _ in range(1_000_000):
        time.sleep(0.015)
        sock.sendto(message.encode(), server_address)

