#!/usr/bin/env python3
"""
This module defines a `Cache` class for interacting with Redis,
and several decorators to track function calls and their history.
"""

import redis
from uuid import uuid4
from typing import Union, Callable, Optional
from functools import wraps


def count_calls(method: Callable) -> Callable:
    """Decorator that counts the number of times a method of the Cache class is called."""
    key = method.__qualname__

    @wraps(method)
    def wrapper(self, *args, **kwargs):
        """Increments the call count each time the method is called."""
        self._redis.incr(key)
        return method(self, *args, **kwargs)
    return wrapper


def call_history(method: Callable) -> Callable:
    """Decorator that stores the input and output history of a method."""
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        """Stores input arguments and the result of the method call in Redis."""
        input = str(args)
        self._redis.rpush(method.__qualname__ + ":inputs", input)
        output = str(method(self, *args, **kwargs))
        self._redis.rpush(method.__qualname__ + ":outputs", output)
        return output
    return wrapper


def replay(fn: Callable):
    """Displays the call history of a decorated function."""
    r = redis.Redis()
    func_name = fn.__qualname__
    c = r.get(func_name)
    try:
        c = int(c.decode("utf-8"))
    except Exception:
        c = 0
    print("{} was called {} times:".format(func_name, c))
    inputs = r.lrange("{}:inputs".format(func_name), 0, -1)
    outputs = r.lrange("{}:outputs".format(func_name), 0, -1)
    for inp, outp in zip(inputs, outputs):
        try:
            inp = inp.decode("utf-8")
        except Exception:
            inp = ""
        try:
            outp = outp.decode("utf-8")
        except Exception:
            outp = ""
        print("{}(*{}) -> {}".format(func_name, inp, outp))


class Cache:
    """Cache class for storing and retrieving data using Redis."""

    def __init__(self):
        """Initialize a Cache instance and clear the Redis database."""
        self._redis = redis.Redis(host='localhost', port=6379, db=0)
        self._redis.flushdb()

    @call_history
    @count_calls
    def store(self, data: Union[str, bytes, int, float]) -> str:
        """
        Store data in Redis and return a unique key.

        Args:
            data: The data to store, which can be of type str, bytes, int, or float.

        Returns:
            A unique string key that identifies the stored data.
        """
        rkey = str(uuid4())
        self._redis.set(rkey, data)
        return rkey

    def get(self, key: str, fn: Optional[Callable] = None) -> Union[str, bytes, int, float]:
        """
        Retrieve data from Redis and optionally apply a conversion function.

        Args:
            key: The key of the data to retrieve.
            fn: An optional callable function to apply to the data for conversion.

        Returns:
            The retrieved data, optionally converted by `fn`.
        """
        value = self._redis.get(key)
        if fn:
            value = fn(value)
        return value

    def get_str(self, key: str) -> str:
        """
        Retrieve a string from Redis by key.

        Args:
            key: The key of the data to retrieve.

        Returns:
            The data as a UTF-8 decoded string.
        """
        value = self._redis.get(key)
        return value.decode("utf-8")

    def get_int(self, key: str) -> int:
        """
        Retrieve an integer from Redis by key.

        Args:
            key: The key of the data to retrieve.

        Returns:
            The data as an integer. If conversion fails, returns 0.
        """
        value = self._redis.get(key)
        try:
            value = int(value.decode("utf-8"))
        except Exception:
            value = 0
        return value

