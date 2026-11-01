from serializer import Serializer
from transport import TransportProtocol

class MessageProtocol:
    def __init__(self, conn):
        self.tp = TransportProtocol(conn)

    def get(self) -> dict | bool:
        """вернёт сообщение или ложь"""
        raw_bytes = self.tp.receive()
        if not raw_bytes:
            return False
        return Serializer.deserialize(raw_bytes)

    def send(self, msg: dict):
        """Метод для отправки сообщения"""
        try:
            raw_bytes = Serializer.serialize(msg)
            self.tp.send(raw_bytes)
        except Exception:
            # Если не ушло, значит клиент отвалился
            pass

    def close(self):
        self.tp.close()