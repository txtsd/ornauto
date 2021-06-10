import logging
import secrets
import time
import uuid
from collections import OrderedDict
from pathlib import Path

import httpx
import requests


class OrnaAccount:
    domain = 'https://playorna.com/api'

    def __init__(self, config):
        self.config = config
        self.username = config['username']
        self.password = config['password']
        self.proxy = config['proxy']
        self.useragent = config['useragent']

        # Apply headers
        self.headers_get = OrderedDict(
            [
                ('accept', "application/json, text/plain, */*"),
                ('cache-control', 'no-cache'),
                ('x-orna-sid', config['x-orna-sid']),
                ('x-orna-version', config['x-orna-version']),
                ('user-agent', config['useragent']),
                ('x-requested-with', config['x-requested-with']),
                ('sec-fetch-site', config['sec-fetch-site']),
                ('sec-fetch-mode', config['sec-fetch-mode']),
                ('sec-fetch-dest', config['sec-fetch-dest']),
                ('accept-encoding', 'gzip, deflate'),
                ('accept-language', 'en-US,en;q=0.9'),
            ]
        )

        self.headers_post = OrderedDict(
            [
                ('content-length', ''),
                ('accept', 'application/json, text/plain, */*'),
                ('cache-control', 'no-cache'),
                ('origin', 'file://'),
                ('x-orna-sid', config['x-orna-sid']),
                ('user-agent', config['useragent']),
                ('content-type', ''),
                ('x-requested-with', config['x-requested-with']),
                ('sec-fetch-site', config['sec-fetch-site']),
                ('sec-fetch-mode', config['sec-fetch-mode']),
                ('sec-fetch-dest', config['sec-fetch-dest']),
                ('accept-encoding', 'gzip, deflate'),
                ('accept-language', 'en-US,en;q=0.9'),
            ]
        )

        # Setup logger
        self.logger = logging.getLogger('autorna.account')

        if (self.proxy != '') and Path.is_file(Path('charles.pem')):
            self.session = httpx.Client(
                http2=True,
                proxies={
                    "http://": self.proxy,
                    "https://": self.proxy,
                },
                verify=False
                # verify='charles.pem'
                # verify='mitmproxy-ca-cert.pem'
            )
        else:
            self.session = httpx.Client(http2=True)

        # Set headers
        self.session.headers = self.headers_get

    # GET

    def get(self, url, params={}, referer='', headers={}):
        if url[0] == '/':
            url = self.domain + url
        if referer != '':
            if referer[0] == '/':
                referer = self.domain + referer
            headers['Referer'] = referer
        params['x'] = int(time.time_ns() / 1000000)
        params['lang'] = 'en'
        result = self.session.get(url, params=params, headers=headers)
        self.session.cookies.clear()
        return result

    # POST
    def post(self, url, data={}, params={}, referer='', headers={}):
        # headers['origin'] = "file://"
        if url[0] == '/':
            url = self.domain + url
        if referer != '':
            if referer[0] == '/':
                referer = self.domain + referer
            headers['Referer'] = referer
        # self.session.headers  # start here
        params['x'] = int(time.time_ns() / 1000000)
        # params['lang'] = 'en'
        data['lang'] = 'en'
        result = self.session.post(url, params=params, data=data, headers=headers)
        self.session.cookies.clear()
        return result
