# locks

*POSIX file system locking using [flock](https://linux.die.net/man/2/flock).*

[![PyPI version](https://img.shields.io/pypi/v/locks)](https://pypi.org/project/locks/)
[![Build status](https://img.shields.io/github/workflow/status/rossmacarthur/locks/build/trunk)](https://github.com/rossmacarthur/locks/actionsquery=workflow%3Abuild)
[![](https://img.shields.io/codecov/c/github/rossmacarthur/locks)](https://codecov.io/gh/rossmacarthur/locks)
[![Code style: black](https://img.shields.io/badge/code%20style-black-101010.svg)](https://github.com/psf/black)

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

Licensed under either of

- Apache License, Version 2.0 ([LICENSE-APACHE](LICENSE-APACHE) or
  http://www.apache.org/licenses/LICENSE-2.0)
- MIT license ([LICENSE-MIT](LICENSE-MIT) or http://opensource.org/licenses/MIT)

at your option.
