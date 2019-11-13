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
        locks = Mutex('/tmp/test.lock')
        assert locks.path == '/tmp/test.lock'
        assert locks.timeout is None
        assert locks._callback is None
        assert locks._fd is None

        locks = Mutex('/tmp/test.lock', timeout=3.14)
        assert locks.path == '/tmp/test.lock'
        assert locks.timeout == 3.14
        assert locks._callback is None
        assert locks._fd is None

        callback = object()
        locks = Mutex('/tmp/test.lock', timeout=3.14, callback=callback)
        assert locks.path == '/tmp/test.lock'
        assert locks.timeout == 3.14
        assert locks._callback is callback
        assert locks._fd is None

    def test___repr__(self):
        locks = Mutex('/tmp/test.lock')
        assert repr(locks) == "locks.Mutex(path='/tmp/test.lock')"

        locks = Mutex('/tmp/test.lock', timeout=3.14)
        assert repr(locks) == "locks.Mutex(path='/tmp/test.lock', timeout=3.14)"

    def test_lock(self):
        _, path = tempfile.mkstemp()

        locks = Mutex(path)
        locks.lock()
        assert os.path.exists(path)

        # check that you can call it again, should basically be a noop
        locks.lock()

        # check that another `Mutex` cannot acquire this one
        locks = Mutex(path, timeout=0.5)
        with raises(BlockingIOError) as e:
            locks.lock()
        assert locks._fd is None
        assert e.value.errno == errno.EAGAIN

    def test_lock_timeout(self):
        _, path = tempfile.mkstemp()

        locks = Mutex(path, timeout=1)
        locks.lock()
        assert os.path.exists(path)

        # check that you can call it again, should basically be a noop
        locks.lock()

        # check that another `Mutex` cannot acquire this one
        locks = Mutex(path, timeout=0.5)
        with raises(BlockingIOError) as e:
            locks.lock()
        assert locks._fd is None
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
        locks = Mutex(path)

        locks.lock()
        assert os.path.exists(path)
        locks.release()
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
    locks = Mutex(path, timeout=0.5)

    def child(locks):
        time.sleep(0.5)
        with raises(BlockingIOError):
            locks.lock()

    p = Process(target=child, args=(locks,))
    p.start()
    locks.lock()
    time.sleep(1)
    locks.release()
    p.join()


def test_multiprocess_double_release():
    _, path = tempfile.mkstemp()
    locks = Mutex(path, timeout=0.5)
    locks.lock()

    def child(locks):
        locks.release()

    p = Process(target=child, args=(locks,))
    p.start()
    time.sleep(1)
    locks.release()
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
