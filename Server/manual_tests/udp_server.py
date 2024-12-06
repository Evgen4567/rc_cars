from datetime import UTC, datetime
import socketserver
import time


NANO_KOEF = 1_000_000_000



count_messages = 0
message_size_total = 0
max_message_size = 0
min_message_size = 0
start_time_ns = time.monotonic_ns()

# Определяем класс-обработчик запросов
class MyUDPHandler(socketserver.BaseRequestHandler):
    def __init__(self, request, client_address, server):
        super().__init__(request, client_address, server)
    
    def handle(self):
        global count_messages
        global message_size_total
        global max_message_size
        global min_message_size
        global start_time_ns
        # Получение данных и адреса клиента
        data, socket = self.request

        count_messages += 1
        current_time_ns = time.monotonic_ns()
        msg_size = len(data)
        message_size_total += msg_size
        max_message_size = max(msg_size, max_message_size)
        min_message_size = min(msg_size, min_message_size)

        if (current_time_ns - start_time_ns) >= 1 * NANO_KOEF:
            start_time_ns = current_time_ns
            dt = datetime.now(tz=UTC)
            print(f"{dt}: {count_messages=}\n{message_size_total=}\n{max_message_size=}\n{min_message_size=}")
            count_messages = 0
            message_size_total = 0
            max_message_size = 0
            min_message_size = 0


# Запуск UDP-сервера
if __name__ == "__main__":
    HOST, PORT = "0.0.0.0", 8000

    with socketserver.UDPServer((HOST, PORT), MyUDPHandler) as server:
        print(f"UDP-сервер запущен на {HOST}:{PORT}")
        server.serve_forever()
