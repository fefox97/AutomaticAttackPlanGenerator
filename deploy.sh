#! /bin/bash
/usr/local/bin/gunicorn --pythonpath ~/WebTesiBs5/ -c ~/WebTesiBs5/gunicorn-cfg.py run:app