#!/usr/bin/env bash

set -ex

if [ "$LINT" = true ]; then
    pip install -r ci/requirements/lint.txt
fi

pip install -r ci/requirements/test.txt .
