#!/usr/bin/env bash
set -ex

# set pip mirror
mkdir ~/.pip
echo '[global]
index-url = http://mirrors.aliyun.com/pypi/simple/

[install]
trusted-host =
  mirrors.aliyun.com' >> ~/.pip/pip.conf

