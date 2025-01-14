# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

# bind = "unix:/home/webapp/sockets/webapp.sock"
workers = 5
accesslog = '-'
loglevel = 'debug'
capture_output = True
enable_stdio_inheritance = True
bind = '0.0.0.0:5000'
timeout = 3000