#!/usr/bin/env bash
set -ex

cd /dist/
pip3 install pipenv
export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8
pipenv install --dev --pre --system --skip-lock

