import socket
from threading import Thread, Lock
from msg_handler import MessageProtocol


class ClientHandler(Thread):
    """Контролирует подключение одного клиента к серверу"""
    def __init__(self, conn, addr, server):
        super().__init__()
        self.server = server
        self.addr = addr
        self.messenger = MessageProtocol(conn)
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
                    print(f"[{self.addr}] {msg['user']}: {msg['text']}")  # отображение в консоли

                    self.server.broadcast(msg, sender=self.username)

        except Exception as e:

            print(f"[!] Возникло исключение {e} c клиентом {self.addr}")
        finally:
            if self.username:
                self.server.remove_user(self.username)
            self.close_connection()
            print(f"[-] Отключен {self.addr}")

    def registration(self) -> bool:
        """заполняет поле username и вносит себя в список(словарь) пользователей на сервере"""

        try:
            self.messenger.send({"user": "Server",
                                 "text": "Регистрация. Пожалуйста, введите имя:",
                                 "status": None})
            while True:
                msg = self.messenger.get()
                if not msg:
                    return False
                username = msg["user"]
                if username:
                    if self.server.add_user(username, self):
                        self.username = username
                        self.messenger.send({"user": "Server",
                                             "text": "Регистрация успешно пройдена",
                                             "status": True})
                        return True
                    else:
                        self.messenger.send({"user": "Server",
                                             "text": "Данное имя уже занято. Попробуйте другое",
                                             "status": False})
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
        self.client_lock = Lock() # замок для работы со списком клиентов

        self.listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Полезная настройка, чтобы порт не "залипал" после перезапуска сервера
        self.listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listener.bind((self.HOST, self.PORT))

    def run(self):
        self.listener.listen(5)
        print("Многопоточный сервер запущен...")
        try:
            while True:
                conn, addr = self.listener.accept()
                handler = ClientHandler(conn, addr, self)
                handler.start()
        except KeyboardInterrupt:
            print("\nСервер останавливает работу")
        finally:
            self.listener.close()

    def add_user(self, name: str, client_handler: ClientHandler) -> bool:
        """если имя не занято, добавляет клиента в словарь"""
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


    def broadcast(self, message_dict, sender=None):
        """Метод для рассылки всем подключенным клиентам."""
        with self.client_lock:
            for username in tuple(self.clients):
                self.clients[username].messenger.send(message_dict)  # сомнительно, но окэй


if __name__ == "__main__":
    server = ChatServer()
    server.run()