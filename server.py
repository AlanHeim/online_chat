from threading import Thread, Lock
from websockets.sync.server import serve
from network_core import MessageProtocol


class ClientHandler(Thread):
    """Контролирует подключение одного клиента к серверу."""

    def __init__(self, ws_conn, addr, server: 'ChatServer'):
        super().__init__()
        self.server = server
        self.addr = addr
        # Передаем готовое WebSocket-соединение в MessageProtocol
        self.messenger = MessageProtocol(ws_conn)
        self.daemon = True
        self.username: str | None = None

    def run(self):
        print(f"[+] Подключен {self.addr}")

        try:
            if self.registration():
                while True:
                    msg = self.messenger.get()
                    if not msg:
                        break
                    print(f"[{self.addr}] {msg['user']}: {msg['text']}")

                    self.server.broadcast(msg)

        except Exception as e:
            print(f"[!] Возникло исключение {e} c клиентом {self.addr}")
        finally:
            if self.username:
                self.server.remove_user(self.username)
            self.close_connection()
            print(f"[-] Отключен {self.addr}")

    def registration(self) -> bool:
        """Заполняет поле username и вносит себя в список пользователей на сервере."""
        try:
            self.messenger.send({
                "user": "Server",
                "text": "Регистрация. Пожалуйста, введите имя:",
                "status": None
            })
            while True:
                msg = self.messenger.get()
                if not msg:
                    return False
                username = msg["user"]
                if username:
                    if self.server.add_user(username, self):
                        self.username = username
                        self.messenger.send({
                            "user": "Server",
                            "text": "Регистрация успешно пройдена",
                            "status": True
                        })
                        return True
                    else:
                        self.messenger.send({
                            "user": "Server",
                            "text": "Данное имя уже занято. Попробуйте другое",
                            "status": False
                        })
        except Exception:
            return False

    def close_connection(self):
        try:
            self.messenger.close()
        except Exception:
            pass


class ChatServer:
    HOST = '127.0.0.1'
    PORT = 5000

    def __init__(self):
        self.clients = {}
        self.client_lock = Lock()

    def run(self):
        print("Многопоточный WebSocket-сервер запущен...")

        def handler(ws_conn):
            """Вызывается автоматически в отдельном потоке на каждое новое подключение."""
            addr = ws_conn.remote_address
            client_thread = ClientHandler(ws_conn, addr, self)
            # Запускаем логику обработки синхронно внутри выделенного потока
            client_thread.run()

        # Запускаем серверный контекст. Он инкапсулирует всю работу с портами под капотом.
        with serve(handler, self.HOST, self.PORT) as server:
            server.serve_forever()

    def add_user(self, name: str, client_handler: ClientHandler) -> bool:
        """Если имя не занято, добавляет клиента в словарь."""
        with self.client_lock:
            if name in self.clients:
                return False
            else:
                self.clients[name] = client_handler
                return True

    def remove_user(self, username: str):
        """Удаление клиента из словаря при отключении."""
        with self.client_lock:
            if username in self.clients:
                del self.clients[username]

    def broadcast(self, message_dict):
        """Метод для рассылки всем подключенным клиентам."""
        with self.client_lock:
            for username in tuple(self.clients):
                self.clients[username].messenger.send(message_dict)


if __name__ == "__main__":
    server = ChatServer()
    server.run()
