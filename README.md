<h1 align="center">locks</h1>
<div align="center">
  <strong>POSIX file system locking using <a href="https://linux.die.net/man/2/flock">flock</a></strong>
</div>
<br />
<div align="center">
  <a href="https://pypi.org/project/locks/">
    <img src="https://img.shields.io/pypi/v/locks" alt="PyPI version" />
  </a>
  <a href="https://github.com/rossmacarthur/locks/actions?query=workflow%3Abuild">
    <img src="https://img.shields.io/github/workflow/status/rossmacarthur/locks/build/master" alt="Build status" />
  </a>
  <a href="https://codecov.io/gh/rossmacarthur/locks" alt="Code coverage">
    <img src="https://img.shields.io/codecov/c/github/rossmacarthur/locks" />
  </a>
  <a href="https://github.com/psf/black">
    <img src="https://img.shields.io/badge/code%20style-black-101010.svg" alt="Code style: black" />
  </a>
</div>

## Getting started

Install this package with

```sh
pip install locks
```

## Usage

The simplest usage is to block indefinitely until the lock is acquired

```python
from locks import Mutex

with Mutex('/tmp/file.lock'):
    # do exclusive stuff here
```

Alternatively, block until a timeout is reached

```python
from locks import Mutex

try:
    with Mutex('/tmp/file.lock', timeout=0.5):
        # do exclusive stuff here
except BlockingIOError:
    # handle the failure to acquire the lock
```

Finally, a common paradigm is to attempt to acquire the lock without blocking,
do something, and then block indefinitely. Here `callback` will be called once
if we cannot immediately acquire the lock, and then we will block indefinitely.

```python
def callback():
    print("Blocking: waiting for file lock on '/tmp/file.lock'")

with Mutex('/tmp/file.lock', callback=callback):
    # do exclusive stuff here
```

If both `callback` and `timeout` are used then we will attempt to
acquire the lock until the `timeout` is reached, and then we will block
indefinitely.

## License

This project is licensed under the MIT License. See the [LICENSE] file.

[LICENSE]: LICENSE
