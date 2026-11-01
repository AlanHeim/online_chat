from typing import Callable
from threading import Thread
from websockets.sync.client import connect
from network_core import MessageProtocol


class ServerListener(Thread):
    """Контейнер, отвечающий ТОЛЬКО за фоновое чтение сообщений от сервера."""

    def __init__(self, msg_protocol: MessageProtocol,
                 on_message_cb: Callable,
                 on_error_cb: Callable
                 ):
        super().__init__()
        self.messenger = msg_protocol
        self.on_message = on_message_cb
        self.on_error = on_error_cb
        self.daemon = True

    def run(self):
        try:
            while True:
                msg = self.messenger.get()
                if not msg:
                    self.on_error("Соединение с сервером потеряно")
                    break
                self.on_message(msg)

        except Exception as e:
            self.on_error(f"[!] Ошибка при получении данных: {e}")


class ChatClient:
    """Главный контейнер клиента, управляющий подключением и отправкой через WebSocket."""
    HOST = '127.0.0.1'
    PORT = 5000

    def __init__(self, on_message_cb: Callable, on_error_cb: Callable):
        self.username = None
        # Формируем стандартный URL для протокола WebSocket
        self.ws_url = f"ws://{self.HOST}:{self.PORT}/"
        self.ws_conn = None
        self.messenger: MessageProtocol | None = None

        self.on_message = on_message_cb
        self.on_error = on_error_cb

        self.is_connected = False

    def initial_connect(self, on_login_msg_cb: Callable) -> bool:
        """Попытка создать подключение (либо проверка, есть ли оно)"""
        try:
            if not self.is_connected:
                # connect открывает TCP-канал, шлет HTTP Upgrade и включает маскирование фреймов
                self.ws_conn = connect(self.ws_url)
                self.messenger = MessageProtocol(self.ws_conn)

                msg = self.messenger.get()
                if msg:
                    on_login_msg_cb(msg)
                self.is_connected = True
            return True
        except Exception as e:
            self.on_error(f"[-] Не удалось подключиться к серверу: {e}")
            return False

    def send_registration_name(self, username: str, on_login_msg_cb: Callable) -> bool:
        """Отправка имени на сервер для регистрации"""
        try:
            self.messenger.send({"user": username})
            msg = self.messenger.get()
            if not msg:
                self.on_error("[!] Соединение с сервером потеряно.")
                return False

            on_login_msg_cb(msg)
            if msg.get("status"):
                self.username = username
                return True
            else:
                return False
        except Exception as e:
            self.on_error(f"Ошибка авторизации. Сбой при проверке имени: {e}")
            return False

    def start_listen_chat(self):
        """Запуск слушателя"""
        listener = ServerListener(self.messenger, self.on_message, self.on_error)
        listener.start()

    def send_message(self, text: str):
        """Отправка обычного сообщения в чат"""
        if self.messenger and text.strip():
            try:
                msg = {"user": self.username, "text": text}
                self.messenger.send(msg)
            except Exception as e:
                self.on_error(f"Не удалось отправить сообщение: {e}")

    def close(self):
        """Корректное закрытие протокола."""
        if self.messenger:
            self.messenger.close()
            self.is_connected = False
