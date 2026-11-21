class LinearProbingHashTable:
    def __init__(self, capacity=8, max_load=0.75):
        if capacity <= 0:
            raise ValueError("capacity must be positive")

        self._slots = [None] * capacity
        self._size = 0
        self._max_load = max_load

    @property
    def capacity(self):
        return len(self._slots)

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
        value, _ = self.get_with_comparisons(key)
        return value

    def get_with_comparisons(self, key):
        index = self._index(key)
        for comparisons in range(1, self.capacity + 1):
            entry = self._slots[index]
            if entry is None:
                return None, comparisons
            stored_key, value = entry
            if stored_key == key:
                return value, comparisons
            index = (index + 1) % self.capacity
        return None, self.capacity

    def probe_indices(self, key):
        index = self._index(key)
        probes = []
        for _ in range(self.capacity):
            probes.append(index)
            entry = self._slots[index]
            if entry is None or entry[0] == key:
                break
            index = (index + 1) % self.capacity
        return tuple(probes)

    def set(self, key, value):
        index = self._index(key)
        for _ in range(self.capacity):
            entry = self._slots[index]
            if entry is None:
                self._slots[index] = (key, value)
                self._size += 1
                if (
                    self._max_load is not None
                    and self._size / self.capacity > self._max_load
                ):
                    self._resize()
                return

            stored_key, _ = entry
            if stored_key == key:
                self._slots[index] = (key, value)
                return
            index = (index + 1) % self.capacity

        raise OverflowError("hash table is full")

    def _resize(self):
        old_slots = self._slots
        self._slots = [None] * (len(old_slots) * 2)
        self._size = 0
        for entry in old_slots:
            if entry is not None:
                key, value = entry
                index = self._index(key)
                while self._slots[index] is not None:
                    index = (index + 1) % self.capacity
                self._slots[index] = (key, value)
                self._size += 1
