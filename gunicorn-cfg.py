# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

bind = "unix:/home/webapp/sockets/webapp.sock"
workers = 1
accesslog = '-'
loglevel = 'debug'
capture_output = True
enable_stdio_inheritance = True
user = 'webapp'
group = 'webapp'