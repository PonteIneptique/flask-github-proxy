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
import base64
import json


def make_secret(data, secret):
    return sha256(bytes("{}{}".format(data.decode("utf-8"), secret), 'utf8')).hexdigest()


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
        self.calls = {}
        self.proxy.github_api_url = ""
        self.client = self.app.test_client()
        self.github_api = make_client(
            "client-id",
            "client-secret",
            {}
        )
        self.github_api_client = self.github_api.test_client()

        def make_request(method, url, **kwargs):
            self.calls["{}::{}".format(method, url.split("?")[0])] = kwargs
            if "params" in kwargs:
                url = "{}?{}".format(
                    url,
                    "&".join(["{}={}".format(key, value) for key, value in kwargs["params"].items()])
                )
                del kwargs["params"]
            return getattr(self.github_api_client, method.lower())(url, **kwargs)

        self.patcher = mock.patch(
            "flask_github_proxy.make_request",
            make_request
        )
        self.mock = self.patcher.start()

    def tearDown(self):
        self.calls = {}
        self.github_api.route_fail = {}
        self.patcher.stop()

    def makeRequest(self, content, secure_sha, data):
        return self.client.post(
            "/perseids/push/path/to/some/file.xml?{}".format(
                "&".join(["{}={}".format(k, v) for k, v in data.items()])
            ),
            data=content,
            headers={"fproxy-secure-hash": secure_sha}
        )

    def test_route_github_put(self):
        """ Test a full put routine

        The test occurs with creation of a new branch
        """
        self.github_api.route_fail[
            "http://localhost/repos/ponteineptique/dummy/contents/path/to/some/file.xml"
        ] = True
        self.github_api.route_fail[
            "http://localhost/repos/ponteineptique/dummy/git/refs/heads/uuid-1234"
        ] = True

        result = self.makeRequest(
            base64.encodebytes(b'Some content'),
            make_secret(base64.encodebytes(b'Some content'), self.secret),
            {
                "author_name": "ponteineptique",
                "date": "19/06/2016",
                "logs": "Hard work of transcribing file",
                "auithor_email": "leponteineptique@gmail.com",
                "branch": "uuid-1234"
            }
        )

        self.assertIn(
            'GET::/repos/ponteineptique/dummy/git/refs/heads/uuid-1234', self.calls.keys(),
            "It should check if the branch exists"
        )
        self.assertIn(
            'GET::/repos/ponteineptique/dummy/git/refs/heads/master', self.calls.keys(),
            "Because it does not exist, it should check for master"
        )
        self.assertIn(
            'POST::/repos/ponteineptique/dummy/git/refs', self.calls.keys(),
            "And it should create a new branch"
        )
        self.assertEqual(
            json.loads(self.calls["POST::/repos/ponteineptique/dummy/git/refs"]["data"]),
            {'ref': 'refs/heads/uuid-1234', 'sha': '123456'},
            "Data pushed should reference to the new branch"
        )
        self.assertIn(
            'GET::/repos/ponteineptique/dummy/contents/path/to/some/file.xml', self.calls.keys(),
            "It should check if files exists"
        )
        self.assertIn(
            'PUT::/repos/ponteineptique/dummy/contents/path/to/some/file.xml', self.calls.keys(),
            "It should make a put as the file does not exist"
        )
        put_data = json.loads(
            self.calls["PUT::/repos/ponteineptique/dummy/contents/path/to/some/file.xml"]["data"]
        )
        put_data["content"] = base64.decodebytes(put_data["content"].encode('utf-8'))
        self.assertEqual(
            {
                "author": {
                    "name": "ponteineptique",
                    "email": "anonymous@github.com"
                },
                "content": b"Some content",
                "message": "Hard work of transcribing file",
                "branch": "uuid-1234"
            },
            put_data
        )
        self.assertIn(
            'POST::/repos/perseusDL/dummy/pulls', self.calls.keys(),
            "It should create a pull request"
        )
        pr = json.loads(self.calls["POST::/repos/perseusDL/dummy/pulls"]["data"])
        self.assertEqual(
            (pr["head"], pr["base"]), ("ponteineptique:uuid-1234", "master"),
            "Origin and upstream should be well set up"
        )
        self.assertEqual(
            result.status_code, 201, "Test should create the PR"
        )
        self.assertEqual(
            json.loads(result.data.decode("utf-8"))["pr_url"], "https://github.com/perseusDL/dummy/pull/9",
            "Test should create the PR and returns its url"
        )

    def test_route_github_update(self):
        self.github_api.sha_origin = "789456"
        result = self.makeRequest(
            base64.encodebytes(b'Some content'),
            make_secret(base64.encodebytes(b'Some content'), self.secret),
            {
                "author_name": "ponteineptique",
                "date": "19/06/2016",
                "logs": "Hard work of transcribing file",
                "branch": "uuid-1234"
            }
        )
        self.assertIn(
            'GET::/repos/ponteineptique/dummy/git/refs/heads/uuid-1234', self.calls.keys(),
            "It should check if the branch exists"
        )
        self.assertNotIn(
            'GET::/repos/ponteineptique/dummy/git/refs/heads/master', self.calls.keys(),
            "Because it exists, it should check for master"
        )
        self.assertNotIn(
            'POST::/repos/ponteineptique/dummy/git/refs', self.calls.keys(),
            "Nor should it create a new branch"
        )
        self.assertIn(
            'POST::/repos/ponteineptique/dummy/contents/path/to/some/file.xml', self.calls.keys(),
            "It should make a post as the file does exist"
        )
        put_data = json.loads(
            self.calls["POST::/repos/ponteineptique/dummy/contents/path/to/some/file.xml"]["data"]
        )
        put_data["content"] = base64.decodebytes(put_data["content"].encode('utf-8'))
        self.assertEqual(
            {
                "author": {
                    "name": "ponteineptique",
                    "email": "anonymous@github.com"
                },
                "content": b"Some content",
                "message": "Hard work of transcribing file",
                "sha": "789456",
                "branch": "uuid-1234"
            },
            put_data,
            "It should post the right data as well as the right sha for the branch"
        )
        self.assertIn(
            'POST::/repos/perseusDL/dummy/pulls', self.calls.keys(),
            "It should create a pull request"
        )
        pr = json.loads(self.calls["POST::/repos/perseusDL/dummy/pulls"]["data"])
        self.assertEqual(
            (pr["head"], pr["base"]), ("ponteineptique:uuid-1234", "master"),
            "Origin and upstream should be well set up"
        )
        self.assertEqual(
            result.status_code, 201, "Test should create the PR"
        )
        self.assertEqual(
            json.loads(result.data.decode("utf-8"))["pr_url"], "https://github.com/perseusDL/dummy/pull/9",
            "Test should create the PR and returns its url"
        )
