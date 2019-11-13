#!/usr/bin/env bash

set -ex

if [ "$LINT" = true ]; then
    black --skip-string-normalization --check .
    flake8 --max-complexity 10 .
fi

pytest -vx --cov=locks --cov-report term-missing --cov-fail-under 100
