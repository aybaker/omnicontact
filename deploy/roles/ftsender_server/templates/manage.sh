#!/bin/bash

export PYTHONPATH=/home/ftsender/deploy/app:/home/ftsender/deploy/local

/home/ftsender/deploy/virtualenv/bin/python \
    /home/ftsender/deploy/app/manage.py $*
