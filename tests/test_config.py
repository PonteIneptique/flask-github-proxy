from unittest import TestCase
from flask import Flask
from flask_github_proxy import GithubProxy


def makeClient(app, **kwargs):
    args = dict(
        prefix="/perseids",
        origin="ponteineptique/dummy",
        upstream="perseusDL/dummy",
        token="client-secret",
        secret="14m3s3cr3t",
        app=app
    )
    args.update(kwargs)
    proxy = GithubProxy(
        **args
    )
    return app.test_client()


class TestIntegration(TestCase):
    def setUp(self):
        self.app = Flask("name")

    def tearDown(self):
        del self.app

    def test_prefix(self):
        client = makeClient(self.app)
        self.assertEqual(
            client.get("/perseids/").status_code, 200,
            "Prefix perseids works"
        )
        client = makeClient(self.app, prefix="/syriaca")
        self.assertEqual(
            client.get("/syriaca/").status_code, 200,
            "Prefix syriaca works"
        )

