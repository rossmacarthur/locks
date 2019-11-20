"""
locks

POSIX file system locking using flock.
"""

import errno
import os
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


class Mutex(object):
    """
    A `Mutex` represents a single exclusive file lock on the local file system.

    The lock is held on a per file descriptor basis, so two instances of
    `Mutex` in the same thread will compete for a lock on the same file path.

    Args:
        path (str): the location of the lock.
        timeout (int/float): how long to block while waiting for the lock.
        callback (callable): if given then the lock will acquired without
            blocking, if that fails then the callback will be called once and
            the `Mutex` will block indefinitely until the lock is acquired.
    """

    def __init__(self, path, timeout=None, callback=None):
        """
        Create a new `Mutex`.
        """
        self.path = path
        self.timeout = timeout
        self._callback = callback
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
            self._fd = os.open(self.path, os.O_RDWR | os.O_CREAT)

        if self._callback or self.timeout is not None:
            end_time = monotonic() + (self.timeout or 0)
            while True:
                try:
                    flock(self._fd, LOCK_EX | LOCK_NB)
                    return
                except (IOError, OSError) as e:
                    if e.errno != errno.EWOULDBLOCK:
                        self._close_fd()
                        raise
                    elif end_time - monotonic() <= 0:
                        if self._callback:
                            self._callback()
                            flock(self._fd, LOCK_EX)
                            return
                        else:
                            self._close_fd()
                            raise
                time.sleep(0.001)
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
