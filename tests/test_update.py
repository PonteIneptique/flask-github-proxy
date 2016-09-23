"""
This file is intended to test integration of the update Route. It offers a replicate of Github API for the commands we cover.
"""
from flask_github_proxy import GithubProxy
from unittest import TestCase
from flask import Flask
import mock
from hashlib import sha256
from tests.github import make_client
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


class TestIntegrationUpdate(TestCase):

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

    def makeRequest(self, secure_sha):
        return self.client.get(
            "/perseids/update",
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
            make_secret(base64.encodebytes(b'master').decode("utf-8"), self.secret)
        )
        self.assertIn(
            'GET::/repos/perseusDL/dummy/git/refs/heads/master', self.calls.keys(),
            "Because it does not exist, it should check for master"
        )
        self.assertIn(
            'PATCH::/repos/ponteineptique/dummy/git/refs/heads/master', self.calls.keys(),
            "Because it does not exist, it should check for master"
        )
        self.assertEqual(
            json.loads(result.data.decode("utf-8")),
            {
                "status": "success",
                "commit": "90e7fe4625c1e7a2cbb0d6384ec06d27a1f52c03"
            }
        )

    def test_route_update_miss_master(self):
        """ Test when the given master branch from upstream does not exist
        """
        # The Branch does not exist
        self.github_api.route_fail[
            "http://localhost/repos/perseusDL/dummy/git/refs/heads/master"
        ] = True
        # The file exist

        result = self.makeRequest(
            make_secret(base64.encodebytes(b'master').decode("utf-8"), self.secret)
        )
        self.assertIn(
            'GET::/repos/perseusDL/dummy/git/refs/heads/master', self.calls.keys(),
            "Because it does not exist, it should check for master"
        )
        self.assertNotIn(
            'PATCH::/repos/ponteineptique/dummy/git/refs/heads/master', self.calls.keys(),
            "Because it does not exist, it should check for master"
        )
        self.assertEqual(
            json.loads(result.data.decode("utf-8")),
            {
                'message': "Upstream Master branch 'master' does not exist",
                'status': 'error',
                'step': 'get_upstream_ref'
            },
            "Missing master upstream should throw an error"
        )

    def test_route_update_fail_master(self):
        """ Test when the given master branch from upstream fails (for any reason)
        """
        # The Branch does not exist
        self.github_api.route_fail[
            "http://localhost/repos/perseusDL/dummy/git/refs/heads/master"
        ] = 401
        # The file exist

        result = self.makeRequest(
            make_secret(base64.encodebytes(b'master').decode("utf-8"), self.secret)
        )
        self.assertIn(
            'GET::/repos/perseusDL/dummy/git/refs/heads/master', self.calls.keys(),
            "Because it does not exist, it should check for master"
        )
        self.assertNotIn(
            'PATCH::/repos/ponteineptique/dummy/git/refs/heads/master', self.calls.keys(),
            "Because it does not exist, it should check for master"
        )
        self.assertEqual(
            json.loads(result.data.decode("utf-8")),
            {'message': 'Bad credentials', 'status': 'error', 'step': 'get_ref'},
            "Failing master ref upstream should throw an error"
        )

    def test_route_update_fail_patch(self):
        """ Test when the given master branch from upstream fails (for any reason)
        """
        # The Branch does not exist
        self.github_api.route_fail[
            "http://localhost/repos/ponteineptique/dummy/git/refs/heads/master"
        ] = "patch"
        # The file exist

        result = self.makeRequest(
            make_secret(base64.encodebytes(b'master').decode("utf-8"), self.secret)
        )
        self.assertIn(
            'GET::/repos/perseusDL/dummy/git/refs/heads/master', self.calls.keys(),
            "Because it does not exist, it should check for master"
        )
        self.assertIn(
            'PATCH::/repos/ponteineptique/dummy/git/refs/heads/master', self.calls.keys(),
            "Because it does not exist, it should check for master"
        )
        self.assertEqual(
            json.loads(result.data.decode("utf-8")),
            {'message': 'Not Found', 'status': 'error', 'step': 'patch'},
            "Failing Patching ref should throw an error"
        )
        self.assertEqual(result.status_code, 404, "Proxy error code should be carried")
