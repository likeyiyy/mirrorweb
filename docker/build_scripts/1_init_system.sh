#!/usr/bin/env bash
set -ex

apt update \
&& apt install -y \
build-essential \
sudo \
python3.5 \
python3-pip \
vim \
locales \
wget \
    && locale-gen 'en_US.UTF-8' \
&& apt-get autoremove \
&& apt-get clean

# set system time zone
ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
