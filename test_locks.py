import errno
import os
import tempfile
import time
from multiprocessing import Process

from mock import Mock
from pytest import raises

from locks import Mutex


try:
    BlockingIOError
except NameError:
    BlockingIOError = (IOError, OSError)


class TestMutex(object):
    def test___init__(self):
        mutex = Mutex('/tmp/test.lock')
        assert mutex.path == '/tmp/test.lock'
        assert mutex.timeout is None
        assert mutex._callback is None
        assert mutex._fd is None

        mutex = Mutex('/tmp/test.lock', timeout=3.14)
        assert mutex.path == '/tmp/test.lock'
        assert mutex.timeout == 3.14
        assert mutex._callback is None
        assert mutex._fd is None

        callback = object()
        mutex = Mutex('/tmp/test.lock', timeout=3.14, callback=callback)
        assert mutex.path == '/tmp/test.lock'
        assert mutex.timeout == 3.14
        assert mutex._callback is callback
        assert mutex._fd is None

    def test_lock(self):
        _, path = tempfile.mkstemp()

        mutex = Mutex(path)
        mutex.lock()
        assert os.path.exists(path)

        # check that you can call it again, should basically be a noop
        mutex.lock()

        # check that another `Mutex` cannot acquire this one
        mutex = Mutex(path, timeout=0.5)
        with raises(BlockingIOError) as e:
            mutex.lock()
        assert mutex._fd is None
        assert e.value.errno == errno.EAGAIN

    def test_lock_timeout(self):
        _, path = tempfile.mkstemp()

        mutex = Mutex(path, timeout=1)
        mutex.lock()
        assert os.path.exists(path)

        # check that you can call it again, should basically be a noop
        mutex.lock()

        # check that another `Mutex` cannot acquire this one
        mutex = Mutex(path, timeout=0.5)
        with raises(BlockingIOError) as e:
            mutex.lock()
        assert mutex._fd is None
        assert e.value.errno == errno.EAGAIN

    def test_lock_callback(self):
        _, path = tempfile.mkstemp()

        def child():
            with Mutex(path):
                time.sleep(1)

        p = Process(target=child)
        callback = Mock()
        p.start()
        time.sleep(0.5)
        with Mutex(path, callback=callback):
            pass
        p.join()
        callback.assert_called_once_with()

    def test_release(self):
        _, path = tempfile.mkstemp()
        mutex = Mutex(path)

        mutex.lock()
        assert os.path.exists(path)
        mutex.release()
        assert not os.path.exists(path)

    def test_with(self):
        _, path = tempfile.mkstemp()

        with Mutex(path):
            assert os.path.exists(path)
        assert not os.path.exists(path)

        with Mutex(path, timeout=0.5):
            assert os.path.exists(path)
        assert not os.path.exists(path)


def test_multiprocess_double_lock():
    _, path = tempfile.mkstemp()
    mutex = Mutex(path, timeout=0.5)

    def child(mutex):
        time.sleep(0.5)
        with raises(BlockingIOError):
            mutex.lock()

    p = Process(target=child, args=(mutex,))
    p.start()
    mutex.lock()
    time.sleep(1)
    mutex.release()
    p.join()


def test_multiprocess_double_release():
    _, path = tempfile.mkstemp()
    mutex = Mutex(path, timeout=0.5)
    mutex.lock()

    def child(mutex):
        mutex.release()

    p = Process(target=child, args=(mutex,))
    p.start()
    time.sleep(1)
    mutex.release()
    p.join()


def test_different_file_descriptors():
    _, path = tempfile.mkstemp()
    a = Mutex(path, timeout=0.5)
    b = Mutex(path, timeout=0.5)

    a.lock()
    with raises(BlockingIOError):
        b.lock()
    a.release()
    a.lock()
    with raises(BlockingIOError):
        b.lock()
