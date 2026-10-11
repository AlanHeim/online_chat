import socket
from threading import Thread
from messenger import Messenger


class ServerListener(Thread):
    def __init__(self, messenger: Messenger):
        super().__init__()
        self.messenger = messenger
        self.daemon = True

    def run(self):
        try:
            while True:
                msg = self.messenger.get()
                if not msg:
                    print("Соеденение потеряно")
                    break
                print(f"{msg["user"]}: {msg["text"]}")
        except Exception as e:
            print(e)


class ChatClient:
    HOST = "127.0.0.1"
    PORT = 5000

    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.messenger = Messenger(self.socket)
        self.username = None

    def connect(self):
        try:
            self.socket.connect((self.HOST, self.PORT))
            if self.registration():
                print("Подключился")
                listener = ServerListener(self.messenger)
                listener.start()
            else:
                print(f"Не удалось подключиться")
                quit()
        except Exception as e:
            print(f"Не удалось подключиться: {e}")
            quit()

    def run(self):
        self.connect()
        try:
            while True:
                # if self.registration():
                words = input("please enter word: ")
                self.messenger.send({"user": self.username, "text": words})
        except (KeyboardInterrupt, EOFError):
            print("Выход из чата")
        finally:
            self.messenger.close()

    def registration(self):
        username = None
        try:
            while True:
                msg = self.messenger.get()
                print(f"{msg["user"]}: {msg["text"]}")
                username = input("Введите своё имя: ")
                self.messenger.send({"user": username})
                msg = self.messenger.get()
                if msg["status"] is True:
                    self.username = username
                    return True
                elif msg["status"] is False:
                    username = input("Введите новое имя: ")

        except:
            return False


if __name__ == "__main__":
    ChatClient().run()
