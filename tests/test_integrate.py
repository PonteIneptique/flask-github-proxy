"""
This file is intended to test integration. It offers a replicate of Github API for the commands we cover.
"""
from flask_github_proxy import GithubProxy
from unittest import TestCase
from flask import Flask
import mock
from hashlib import sha256
from .github import make_client
import base64
import json


def make_secret(data, secret):
    return sha256(bytes("{}{}".format(data, secret), 'utf8')).hexdigest()


def response_read(response):
    """ Read a response, returns data and status code

    :param response: Flask Response / Request Response
    :return: Decoded Json and Status Code
    :rtype: (dict, int)
    """
    return json.loads(response.data.decode("utf-8")), response.status_code


class TestIntegration(TestCase):

    def setUp(self):
        self.app = Flask("name")
        self.secret = "14m3s3cr3t"
        self.proxy = GithubProxy(
            "/perseids",
            "ponteineptique/dummy",
            "perseusDL/dummy",
            token="client-id",
            secret=self.secret,
            app=self.app
        )
        self.calls = {}
        self.proxy.github_api_url = ""
        self.client = self.app.test_client()
        self.github_api = make_client(
            "client-id",
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
            data = getattr(self.github_api_client, method.lower())(url, **kwargs)
            data.content = data.data
            return data

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

    def test_route_github_update(self):
        """ Test a full file update routine

        The test occurs with creation of a new branch
        """
        # The Branch does not exist
        self.github_api.route_fail[
            "http://localhost/repos/ponteineptique/dummy/git/refs/heads/uuid-1234"
        ] = True
        # The file exist
        self.github_api.exist_file["path/to/some/file.xml"] = True

        result = self.makeRequest(
            base64.encodebytes(b'Some content'),
            make_secret(base64.encodebytes(b'Some content').decode("utf-8"), self.secret),
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
                "branch": "uuid-1234",
                "sha": '123456'
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

    def test_route_github_create(self):
        """ Test a file creation
        """
        self.github_api.sha_origin = "789456"
        self.github_api.exist_file["path/to/some/file.xml"] = False
        result = self.makeRequest(
            base64.encodebytes(b'Some content'),
            make_secret(base64.encodebytes(b'Some content').decode("utf-8"), self.secret),
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
            'PUT::/repos/ponteineptique/dummy/contents/path/to/some/file.xml', self.calls.keys(),
            "It should make a put as the file does exist"
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

    def test_error_content_missing(self):
        """ Test error on missing content
        """
        self.github_api.sha_origin = "789456"
        self.github_api.exist_file["path/to/some/file.xml"] = False
        result = self.makeRequest(
            b"",
            make_secret(base64.encodebytes(b'').decode("utf-8"), self.secret),
            {
                "author_name": "ponteineptique",
                "date": "19/06/2016",
                "logs": "Hard work of transcribing file",
                "branch": "uuid-1234"
            }
        )
        data, http = response_read(result)
        self.assertEqual(
            data, {'message': 'Content is missing', 'status': 'error'},
            "Explain error when content is missing"
        )
        self.assertEqual(http, 300, "300 is the http code for content missing")

    def test_error_content_sha_is_wrong(self):
        """ Test that wrong secure would fail
        """
        self.github_api.sha_origin = "789456"
        self.github_api.exist_file["path/to/some/file.xml"] = False
        result = self.makeRequest(
            b"Encoded Content",
            make_secret(base64.encodebytes(b'Not the right sha').decode("utf-8"), self.secret),
            {
                "author_name": "ponteineptique",
                "date": "19/06/2016",
                "logs": "Hard work of transcribing file",
                "branch": "uuid-1234"
            }
        )
        data, http = response_read(result)
        self.assertEqual(
            data, {'message': 'Hash does not correspond with content', 'status': 'error'},
            "Explain error when hash is wrong"
        )
        self.assertEqual(http, 300, "300 is the http code when hash is wrong")

    def test_error_get_ref_failure(self):
        """ Test that github api check ref fails does not break API
        """
        self.github_api.sha_origin = "789456"
        self.github_api.exist_file["path/to/some/file.xml"] = False
        self.github_api.route_fail[
            "http://localhost/repos/ponteineptique/dummy/git/refs/heads/uuid-1234"
        ] = 500
        result = self.makeRequest(
            base64.encodebytes(b'Some content'),
            make_secret(base64.encodebytes(b'Some content').decode("utf-8"), self.secret),
            {
                "author_name": "ponteineptique",
                "date": "19/06/2016",
                "logs": "Hard work of transcribing file",
                "auithor_email": "leponteineptique@gmail.com",
                "branch": "uuid-1234"
            }
        )
        data, http = response_read(result)
        self.assertEqual(
            data, {'message': 'Bad credentials', 'status': 'error'},
            "Error message should be carried by ProxyError in Ref Failure"
        )
        self.assertEqual(http, 401, "Status code should be carried by ProxyError")

    def test_error_make_ref_failure(self):
        """ Test that github api make ref fails does not break API
        """
        self.github_api.sha_origin = "789456"
        self.github_api.exist_file["path/to/some/file.xml"] = False
        # We need to make checking the ref fail first (because the branch should not exist to trigger creation)
        self.github_api.route_fail[
            "http://localhost/repos/ponteineptique/dummy/git/refs/heads/uuid-1234"
        ] = True
        # And then make creating fail
        self.github_api.route_fail[
            "http://localhost/repos/ponteineptique/dummy/git/refs"
        ] = True
        result = self.makeRequest(
            base64.encodebytes(b'Some content'),
            make_secret(base64.encodebytes(b'Some content').decode("utf-8"), self.secret),
            {
                "author_name": "ponteineptique",
                "date": "19/06/2016",
                "logs": "Hard work of transcribing file",
                "auithor_email": "leponteineptique@gmail.com",
                "branch": "uuid-1234"
            }
        )
        data, http = response_read(result)
        self.assertEqual(
            data, {'message': 'Not Found', 'status': 'error'},
            "Error message should be carried by ProxyError in Ref Creation Failure"
        )
        self.assertEqual(http, 404, "Status code should be carried by ProxyError")
