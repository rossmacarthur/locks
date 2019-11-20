"""
locks

POSIX file system locking using flock.
"""

import errno
import os
import random
import time
from fcntl import LOCK_EX, LOCK_NB, LOCK_UN, flock

from monotonic import monotonic


__all__ = ['Mutex']
__title__ = 'locks'
__version__ = '0.1.1'
__url__ = 'https://github.com/rossmacarthur/locks'
__author__ = 'Ross MacArthur'
__author_email__ = 'ross@macarthur.io'
__license__ = 'MIT'
__description__ = 'POSIX file system locking using flock'


class Waiter(object):
    """
    A `Waiter` defines a waiting style when trying to acquire a lock with a
    non-blocking way. The `__call__()` method sleeps until we should try attempt
    to acquire the lock again.

    This class should be subclassed.
    """

    def __init__(self):
        pass

    def __call__(self):
        raise NotImplementedError('this method should be overridden')


class ConstantWaiter(Waiter):
    """
    Wait a constant amount of time. This is sufficient when there are very few
    threads/processes trying to access the lock.
    """

    def __init__(self, delay):
        self.delay = delay

    def __call__(self):
        return self.delay


class RandomWaiter(Waiter):
    """
    Wait a random amount of time. This can handle very many processes but does
    not give longer waiting processes any advantage.
    """

    def __init__(self, min_delay, max_delay):
        self.min_delay = min_delay
        self.max_delay = max_delay

    def __call__(self):
        return random.uniform(self.min_delay, self.max_delay)


class Mutex(object):
    """
    A `Mutex` represents a single exclusive file lock on the local file system.

    The lock is held on a per file descriptor basis, so two instances of
    `Mutex` in the same thread will compete for a lock on the same file path.

    Args:
        path (str): the location of the lock.
        timeout (int/float): how long to block while waiting for the lock.
        waiter (Waiter): a waiter to use when trying to acquire a lock in a
            non-blocking way.
        callback (callable): if given then the lock will acquired without
            blocking, if that fails then the callback will be called once and
            the `Mutex` will block indefinitely until the lock is acquired.
    """

    def __init__(self, path, timeout=None, waiter=None, callback=None):
        """
        Create a new `Mutex`.
        """
        self.path = path
        self.timeout = timeout
        self._callback = callback
        self._waiter = waiter

        if not self._waiter and (self._callback or self.timeout is not None):
            self._waiter = ConstantWaiter(0.001)

        self._fd = None

    def _close_fd(self):
        if self._fd:
            flock(self._fd, LOCK_UN)
            os.close(self._fd)
            self._fd = None

    def lock(self):
        """
        Attempt to acquire the file lock, blocks until the configured timeout.

        If the timeout is 0 then a single attempt will be made to acquire the
        lock and it will not block.
        """
        if not self._fd:
            self._fd = os.open(self.path, os.O_CREAT | os.O_RDWR)

        if self._callback or self.timeout is not None:
            end_time = monotonic() + (self.timeout or 0)
            while True:
                try:
                    flock(self._fd, LOCK_EX | LOCK_NB)
                    return
                except (IOError, OSError) as e:
                    remaining = end_time - monotonic()
                    if e.errno != errno.EWOULDBLOCK:
                        self._close_fd()
                        raise
                    elif remaining <= 0:
                        if self._callback:
                            self._callback()
                            flock(self._fd, LOCK_EX)
                            return
                        else:
                            self._close_fd()
                            raise
                time.sleep(min(remaining, self._waiter()))
        else:
            flock(self._fd, LOCK_EX)

    def release(self):
        """
        Release the lock.
        """
        self._close_fd()

        # Not critical to locking behaviour, but remove the file for user
        # visibility.
        try:
            os.unlink(self.path)
        except (IOError, OSError):
            pass

    def __enter__(self):
        """
        Allow use of the `Mutex` in a `with` statement.
        """
        self.lock()
        return self

    def __exit__(self, type, value, traceback):
        """
        Allow use of the `Mutex` in a `with` statement.
        """
        return self.release()
