#!/usr/bin/env bash
# exit on error
set -o errexit

# flask db init
# flask db migrate
# flask db upgrade

# start the server
gunicorn --config "gunicorn-cfg.py" run:app
