#!/usr/bin/env python

"""
Written by Piyush Verma
Email: piyushv@vmware.com

Helper to run command in remote
"""
import requests

s = requests.Session()
s.auth = ('admin', 'Admin!23')

s.get("https://10.160.14.148/api/v1/logical-ports")