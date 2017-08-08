# coding=utf-8
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import re
import json
import logging
import datetime

import requests


class GitHub(object):
    """Base class GitHub"""
    DEBUG = True
    API_URL = "https://api.github.com"
    HEADER = {
        "Accept": "application/vnd.github.mercy-preview+json"
    }

    def configure(self, token):
        self.HEADER["Authentication"] = "token {}".format(token)

    def since_days(self, days=30):
        return str(datetime.date.today() - datetime.timedelta(days))


class GitHubCommitMonitor(GitHub):
    URL_TEMPLATE = "https://api.github.com/repos/{user}/{repo}/commits"

    def __init__(self, repository, keywords, flags=0):
        self.keywords = keywords
        self.flags = flags
        self.constraint = '\s?({})(\s|\.|:\s)?'
        self.url = self.URL_TEMPLATE.format(**repository)
        self.params = {
            'since': self.since_days(repository['since']),
            'page': 0,
            'sha': repository['branch']
        }
        self.results = []

    def start(self):
        while True:
            response = requests.get(self.url, headers=self.HEADER, params=self.params)
            commits = response.json()

            self._check_rate_limit(commits)

            for commit in commits:
                result = self._search(commit)
                if result:
                    self.results.append(result)
                    logging.info(result)

            if not re.match('<(?P<next>.+)>; rel="next"', response.headers.get('Link', '')):
                break
            # GitHub API bug? "next" link is of different REST request.
            self.params['page'] = int(self.params['page']) + 1

    def _check_rate_limit(self, response):
        # https://developer.github.com/v3/oauth_authorizations/# create-a-new-authorization
        if "message" in response and "rate limit" in response["message"]:
            raise Exception(response["message"])

    def _search(self, commit):
        message = commit['commit']['message']
        for name, expressions in self.keywords.items():
            for regex in expressions:
                constraint = self.constraint.format(regex)
                for match in re.finditer(constraint, message, self.flags):
                    if match.group(0) != match.group(1):
                        result = {
                            "message": message,
                            "url": commit["commit"]["url"]
                        }
                        return result
