"""
This file is intended to test integration. It offers a replicate of Github API for the commands we cover.
"""
from flask_github_proxy import GithubProxy
from unittest import TestCase
from flask import Flask
import mock
from io import BytesIO
from hashlib import sha256
from github import make_client


def make_secret(data, secret):
    return sha256(bytes("{}{}".format(data, secret), 'utf8')).hexdigest()


class TestIntegration(TestCase):

    def setUp(self):
        self.app = Flask("name")
        self.secret = "14m3s3cr3t"
        self.proxy = GithubProxy(
            "/perseids",
            "ponteineptique/dummy",
            "perseusDL/dummy",
            github_id="client-id",
            github_secret="client-secret",
            secret=self.secret,
            app=self.app
        )
        self.calls = []
        self.proxy.github_api_url = ""
        self.client = self.app.test_client()
        self.github_api = make_client("client-id", "client-secret").test_client()

        def make_request(method, url, **kwargs):
            self.calls.append((method, url, kwargs))
            return getattr(self.github_api, method.lower())(url, **kwargs)

        self.patcher = mock.patch(
            "flask_github_proxy.make_request",
            make_request
        )
        self.mock = self.patcher.start()

    def tearDown(self):
        self.calls = []
        self.patcher.stop()

    def makeRequest(self, content, data):
        return self.client.post(
            "/perseids/push/path/to/some/file.xml?{}".format(
                "&".join(["{}={}".format(k, v) for k, v in data.items()])
            ),
            data={"content": content}
        )

    def test_route_receive(self):
        data = self.makeRequest(
            (BytesIO(b'Some content'), 'file.xml'),
            {
                "author": "ponteineptique",
                "date": "19/06/2016",
                "logs": "Hard work of transcribing file",
                "sha": make_secret("Some content", self.secret)
            }
        )
        print(self.calls)
        self.assertEqual(data, [])
