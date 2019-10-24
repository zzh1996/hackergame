#!/bin/bash

./manage.py migrate
./manage.py collectstatic --noinput
uwsgi conf/uwsgi-apps/docker.ini
