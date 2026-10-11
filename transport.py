import socket


class TransportProtocol:
    """Управляет низкоуровневой отправкой и чтением байт."""

    def __init__(self, conn: socket.socket):
        self.conn = conn

    def send(self, raw_bytes: bytes):
        """Прикрепляет 4 байта длины и отправляет в сокет."""
        length = len(raw_bytes).to_bytes(4, 'big')
        self.conn.sendall(length + raw_bytes)  # гарантирует отправку всех данных, в отличие от обычного send

    def receive(self) -> bytes:
        """Читает 4 байта длины, а затем дочитывает точное количество байт."""
        raw_len = self.conn.recv(4)
        if not raw_len:
            return b""
        length = int.from_bytes(raw_len, 'big')

        # Правильное дочитывание буфера (вдруг данные пришли частями)
        data = b""
        while len(data) < length:
            chunk = self.conn.recv(length - len(data))
            if not chunk:
                break
            data += chunk
        return data

    def close(self):
        self.conn.close()

