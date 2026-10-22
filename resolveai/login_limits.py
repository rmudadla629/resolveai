"""Bounded, thread-safe login attempt windows for a single local process."""

import math
import threading
import time


class LoginLimiter:
    def __init__(self, limit=5, window=60, capacity=4096, clock=time.monotonic):
        self.limit = limit
        self.window = window
        self.capacity = capacity
        self.clock = clock
        self.entries = {}
        self.lock = threading.Lock()

    def check(self, key):
        """Reserve an attempt before password hashing; return retry seconds or 0."""
        with self.lock:
            now = self.clock()
            for stale in [k for k, (end, _) in self.entries.items() if end <= now]:
                del self.entries[stale]
            if key not in self.entries:
                if len(self.entries) >= self.capacity:
                    return max(1, math.ceil(min(end for end, _ in self.entries.values()) - now))
                self.entries[key] = (now + self.window, 0)
            end, attempts = self.entries[key]
            if attempts >= self.limit:
                return max(1, math.ceil(end - now))
            self.entries[key] = (end, attempts + 1)
            return 0


limiter = LoginLimiter()
