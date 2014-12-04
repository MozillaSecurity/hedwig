#!/usr/bin/env python3
# coding=utf-8
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import re
import json
import base64
import urllib.request
import datetime


class CommitMonitor(object):
    URL_TEMPLATE = 'https://api.github.com/repos/{user}/{repo}/commits?per_page=100&sha={branch}&since={since}'

    def __init__(self, github, config, keywords, flags=0):
        self.github = github
        self.keywords = keywords
        self.flags = flags
        self.contraint = '\s?({})(\s|\.|:\s)?'
        self.URL = CommitMonitor.URL_TEMPLATE.format(**config)

    def start(self):
        while True:
            if GitHub.DEBUG:
                print(self.URL)
            response = self.github.request.open(self.URL)
            header = dict(response.info())
            commits = json.loads(response.read().decode("latin-1"))
            for commit in commits:
                message = commit['commit']['message']
                for id_name, keyword_group in self.keywords.items():
                    for regex in keyword_group.keys():
                        constraint = self.contraint.format(regex)
                        for match in re.finditer(constraint, message, self.flags):
                            if match.group(0) != match.group(1):
                                self.keywords[id_name][regex] += 1
                                break
            next_page = re.match('<(?P<next>.+)>; rel="next"', header.get('Link', ''))
            if not next_page:
                break
            self.URL = next_page.group("next")

    def result(self):
        r = {}
        for name, regex_group in self.keywords.items():
            r[name] = sum(regex_group.values())
        return r

    def __str__(self):
        s = ""
        r = self.result()
        for name in sorted(r, key=r.get, reverse=True):
            s += "{}:{} ".format(name, r[name])
        return s


class GitHub(object):
    """Base class GitHub"""
    API_URL = "https://api.github.com"
    DEBUG = True

    class HTTPBasicPriorAuthHandler(urllib.request.HTTPBasicAuthHandler):
        """Bug: http://bugs.python.org/issue19494"""
        handler_order = 400

        def http_request(self, req):
            if not req.has_header('Authorization'):
                user, passwd = self.passwd.find_user_password(None, req.host)
                credentials = '{0}:{1}'.format(user, passwd).encode()
                auth_str = base64.standard_b64encode(credentials).decode()
                req.add_unredirected_header('Authorization', 'Basic {}'.format(auth_str.strip()))
            return req

        https_request = http_request

    def __init__(self, creds):
        if not (isinstance(creds, tuple) or isinstance(creds, list)) or len(creds) != 2:
            raise ValueError("Credentials must be a tuple or list")
        auth_handler = GitHub.HTTPBasicPriorAuthHandler(urllib.request.HTTPPasswordMgrWithDefaultRealm())
        auth_handler.add_password(realm=None, uri=GitHub.API_URL, user=creds[0], passwd=creds[1])
        self.request = urllib.request.build_opener(auth_handler)

    def since_days(self, days=30):
        return str(datetime.date.today() - datetime.timedelta(days))

    def monitor_commits(self, config, keywords, flags=0):
        monitor = CommitMonitor(self, config, keywords, flags)
        try:
            monitor.start()
        except Exception as ex:
            print(ex)
        finally:
            return monitor


if __name__ == "__main__":
    keywords = {
        "JPG": {"JPG|JPEG|libjpeg-turbo": 0},
        "ICO": {"ICO": 0},
        "PNG": {"PNG": 0},
        "GIF": {"GIF": 0},
        "BMP": {"BMP": 0},
        "WOFF": {"WOFF|Woff": 0},
        "Theora": {"Theora|theora": 0},
        "Vorbis": {"Vorbis|vorbis": 0},
        "Opus": {"libopus|Opus|opus": 0},
        "OGG": {"Ogg|OGG": 0},
        "WebM": {"WebM|VPX|vpx": 0},
        "MP4": {"MP4|H264": 0},
        "MP3": {"MP3": 0},
        "Stagefright": {"Stagefright": 0},
        "WAV": {"WAV": 0},
        "IPC": {"IPC": 0},
        "NFC": {"NFC|Nfc": 0},
        "MediaRecorder": {"MediaRecorder": 0},
        "WebAudio": {"WebAudio": 0},
        "WebCrypto": {"WebCrypto": 0},
        "WebRTC": {"WebRTC": 0},
        "WebVTT": {"WebVTT": 0},
        "WebGL": {"WebGL": 0},
        "GMP": {"GMP": 0},
        "SVG": {"SVG": 0},
        "MathML": {"MathML": 0},
        "Canvas2D": {"Canvas2D": 0},
        "SPDY": {"SPDY|Spdy": 0},
        "HTTP2": {"Http2|HTTP2": 0},
        "WebSocket": {"WebSocket": 0}
    }
    git = GitHub(("username", "password"))
    github_firefox = {'since': git.since_days(30), 'user': 'mozilla', 'repo': 'gecko-dev', 'branch': 'inbound'}
    try:
        monitor = git.monitor_commits(github_firefox, keywords, 2)
    except KeyboardInterrupt:
        pass
    print(monitor)
