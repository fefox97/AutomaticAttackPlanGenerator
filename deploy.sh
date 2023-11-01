#! /bin/bash
/home/webapp/.pyenv/versions/3.11.6/envs/WebApp/bin/gunicorn --pythonpath ~/WebTesiBs5/ -c ~/WebTesiBs5/gunicorn-cfg.py run:app