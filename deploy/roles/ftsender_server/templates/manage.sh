#!/bin/bash

/home/ftsender/deploy/virtualenv/bin/python \
    --pythonpath=/home/ftsender/deploy/app \
    --pythonpath=/home/ftsender/deploy/local \
    /home/ftsender/deploy/app/manage.py $*
