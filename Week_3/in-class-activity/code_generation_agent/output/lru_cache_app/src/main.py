from collections import OrderedDict
from typing import Optional


class LRUCache:
    """
    Least Recently Used (LRU) Cache implementation using OrderedDict.
    Uses only in-memory structures; no external or user data.
    """

    def __init__(self, capacity: int) -> None:
        if capacity <= 0:
            raise ValueError("Capacity must be a positive integer")
        self.capacity = capacity
        self.cache: OrderedDict[int, int] = OrderedDict()

    def get(self, key: int) -> int:
        """Return value for key, or -1 if not found."""
        if key not in self.cache:
            return -1
        self.cache.move_to_end(key)
        return self.cache[key]

    def put(self, key: int, value: int) -> None:
        """Insert or update key-value. Evicts LRU item if at capacity."""
        if key in self.cache:
            self.cache.move_to_end(key)
        else:
            if len(self.cache) >= self.capacity:
                self.cache.popitem(last=False)
        self.cache[key] = value


if __name__ == "__main__":
    cache = LRUCache(2)
    cache.put(1, 1)
    cache.put(2, 2)
    print(cache.get(1))   # 1
    cache.put(3, 3)        # evicts key 2
    print(cache.get(2))    # -1
    print(cache.get(3))    # 3
