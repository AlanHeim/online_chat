from json import loads, dumps

class Serializer:
    """Отвечает за кодирование и декодирование JSON-сообщений"""
    @staticmethod
    def deserialize(raw_bytes: bytes) -> dict:
        """байты в словарь."""
        json_str = raw_bytes.decode('utf-8')
        return loads(json_str)

    @staticmethod
    def serialize(message_dict: dict) -> bytes:
        """словарь в байты"""
        json_str = dumps(message_dict, ensure_ascii=False)
        return json_str.encode('utf-8')
