from websockets.exceptions import ConnectionClosed


class TransportProtocol:
    """Универсальный синхронный транспорт для отправки и чтения сырых байт через WebSocket."""

    def __init__(self, ws_connection):
        self.ws = ws_connection

    def send(self, raw_bytes: bytes):
        """Отправляет сырые байты в бинарном кадре WebSocket (Opcode 0x2)."""
        try:
            self.ws.send(raw_bytes)
        except ConnectionClosed:
            pass

    def receive(self) -> bytes:
        """Блокирует поток до получения цельного фрейма данных.

        Гарантированно возвращает объект типа bytes.
        """
        try:
            data = self.ws.recv()
            # Библиотека может вернуть str, если удаленная сторона послала текстовый кадр.
            # Наш контракт требует strictly bytes, поэтому принудительно переводим в байты.
            return data
        except ConnectionClosed:
            return b""

    def close(self):
        """Корректно закрывает WebSocket соединение, отправляя Close-фрейм."""
        try:
            self.ws.close()
        except Exception:
            pass
