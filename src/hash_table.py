class HashTable:
    def __init__(self):
        self._buckets = [[] for _ in range(8)]
        self._size = 0

    @property
    def capacity(self):
        return len(self._buckets)

    def __len__(self):
        return self._size

    def _index(self, key):
        if not isinstance(key, str):
            raise TypeError("key must be a string")

        value = 0
        for character in key:
            value = 31 * value + ord(character)
        return value % self.capacity

    def get(self, key):
        bucket = self._buckets[self._index(key)]
        for stored_key, value in bucket:
            if stored_key == key:
                return value
        return None

    def set(self, key, value):
        index = self._index(key)
        bucket = self._buckets[index]
        for entry_index, (stored_key, _) in enumerate(bucket):
            if stored_key == key:
                bucket[entry_index] = (key, value)
                return

        bucket.append((key, value))
        self._size += 1
        if self._size / self.capacity > 0.75:
            self._resize()

    def _resize(self):
        old_buckets = self._buckets
        self._buckets = [[] for _ in range(len(old_buckets) * 2)]

        for bucket in old_buckets:
            for key, value in bucket:
                self._buckets[self._index(key)].append((key, value))
