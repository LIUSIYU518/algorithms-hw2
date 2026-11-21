from urllib.parse import urlsplit

from src.base62 import decode, encode
from src.hash_table import HashTable
from src.linear_probing import LinearProbingHashTable


class URLShortener:
    def __init__(self, strategy="chaining"):
        if strategy == "chaining":
            table_class = HashTable
        elif strategy == "linear_probing":
            table_class = LinearProbingHashTable
        else:
            raise ValueError("strategy must be 'chaining' or 'linear_probing'")

        self.strategy = strategy
        self._url_to_code = table_class()
        self._code_to_url = table_class()
        self._next_id = 1

    @staticmethod
    def _is_valid_url(url):
        if not isinstance(url, str):
            raise TypeError("url must be a string")
        if not url or any(character.isspace() for character in url):
            return False

        try:
            parsed = urlsplit(url)
            hostname = parsed.hostname
            parsed.port
        except ValueError:
            return False

        return parsed.scheme in ("http", "https") and bool(hostname)

    def shorten(self, url):
        if not self._is_valid_url(url):
            raise ValueError("url must be an absolute HTTP or HTTPS URL")

        existing_code = self._url_to_code.get(url)
        if existing_code is not None:
            return existing_code

        code = encode(self._next_id)
        while self._code_to_url.get(code) is not None:
            self._next_id += 1
            code = encode(self._next_id)

        self._next_id += 1
        self._url_to_code.set(url, code)
        self._code_to_url.set(code, url)
        return code

    def expand(self, code):
        if not isinstance(code, str) or not code:
            return None
        try:
            decode(code)
        except ValueError:
            return None
        return self._code_to_url.get(code)
