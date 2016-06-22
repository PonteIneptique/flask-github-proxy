from flask import Flask, Blueprint, request, jsonify
from copy import deepcopy
from hashlib import sha256
import datetime
import base64
import json
from requests import request as make_request


class Author(object):
    def __init__(self, name, email):
        self.__name__ = name
        self.__email__ = email

    @property
    def name(self):
        return self.__name__

    @property
    def email(self):
        return self.__email__

    def dict(self):
        return {
            "name": self.name,
            "email": self.email
        }


class File(object):
    """

    :param path:
    :param content:
    :param author:
    :param date:
    :param logs:
    :return:
    """
    def __init__(self, path, content, author, date, logs):
        self.__path__ = path
        self.__content__ = content
        self.__author__ = author
        self.__date__ = date
        self.__logs__ = logs
        self.blob = None

    @property
    def path(self):
        return self.__path__

    @property
    def content(self):
        return self.__content__

    @property
    def author(self):
        return self.__author__

    @property
    def date(self):
        return self.__date__

    @property
    def logs(self):
        return self.__logs__

    def sha_secret(self, secret):
        if secret:
            return sha256(self.content.read() + secret).hexdigest()

    @property
    def sha(self):
        return sha256(self.content.read()).hexdigest()

    def dict(self):
        params = {
            prop: getattr(self, prop)
            for prop in [
                "logs", "date", "author", "sha", "path"
            ]
        }
        params["author"] = params["author"].dict()
        return params

    def base64(self):
        return base64.encodebytes(self.content.read()).decode("utf-8")


class GithubProxy(object):
    """ Provides routes to push files to github and open pull request as a service

    :param path: URI Prefix (Has to start with "/")
    :param source_repo:
    :param target_repo:
    :param app:

    """

    URLS = [
        ("/push/<path:filename>", "r_receive", ["POST"])
    ]

    DEFAULT_AUTHOR = Author(
        "Github Proxy",
        "anonymous@github.com"
    )

    def __init__(self,
                 prefix, source_repo, target_repo,
                 secret,
                 github_secret, github_id,
                 app=None, default_author=None):

        self.__blueprint__ = None
        self.__prefix__ = prefix
        self.__name__ = prefix.replace("/", "_").replace(".", "_")
        self.__source_repo__ = source_repo
        self.__target_repo__ = target_repo
        self.__secret__ = secret
        self.__urls__ = deepcopy(type(self).URLS)
        self.__default_author__ = default_author

        self.github_secret = github_secret
        self.github_id = github_id
        self.github_api_url = "https://api.github.com"
        if not default_author:
            self.__default_author__ = GithubProxy.DEFAULT_AUTHOR

        if app is not None:
            self.app = app
            self.init_app(self.app)
        else:
            self.app = None

    def request(self, method, url, **kwargs):
        if "params" not in kwargs:
            kwargs["params"] = {}
        kwargs["params"]["client_id"] = self.github_id
        kwargs["params"]["client_secret"] = self.github_secret

        return make_request(
            method,
            url,
            **kwargs
        )

    @property
    def secret(self):
        return self.__secret__

    @property
    def blueprint(self):
        return self.__blueprint__

    @property
    def prefix(self):
        return self.__prefix__

    @property
    def name(self):
        return self.__name__

    @property
    def source_repo(self):
        return self.__source_repo__

    @property
    def target_repo(self):
        return self.__target_repo__

    @property
    def default_author(self):
        return self.__default_author__

    def init_app(self, app):
        """ Initialize the application and register the blueprint

        :param app:

        :return: Blueprint of the current nemo app
        :rtype: flask.Blueprint
        """
        self.__blueprint__ = Blueprint(
            self.__name__,
            self.__name__,
            url_prefix=self.__prefix__,
        )

        for url, name, methods in self.__urls__:
            self.blueprint.add_url_rule(
                url,
                view_func=getattr(self, name),
                endpoint=name.replace("r_", ""),
                methods=methods
            )
        self.app = self.app.register_blueprint(self.blueprint)

        return self.blueprint

    def put(self, file):
        data = self.request(
            "PUT",
            "{api}/repos/{source_repo}/contents/{path}".format(
                api=self.github_api_url,
                source_repo=self.source_repo,
                path=file.path
            ),
            data=json.dumps({
                "message": file.logs,
                "author": file.author.dict(),
                "content": file.base64()
            })
        )
        return json.loads(data.data.decode("utf-8"))

    def get(self, file):
        data = self.request(
            "GET",
            "{api}/repos/{source_repo}/contents/{path}".format(
                api=self.github_api_url,
                source_repo=self.source_repo,
                path=file.path
            )
        )
        # We update the file blob because it exists and we need it for update
        if data.status_code == 200:
            reply = json.loads(data.data.decode("utf-8"))
            file.blob = reply["sha"]

        return data

    def update(self, file):
        data = self.request(
            "POST",
            "{api}/repos/{source_repo}/contents/{path}".format(
                api=self.github_api_url,
                source_repo=self.source_repo,
                path=file.path
            ),
            data=json.dumps({
                "message": file.logs,
                "author": file.author.dict(),
                "content": file.base64(),
                "blob": file.blob
            })
        )
        return json.loads(data.data.decode("utf-8"))

    def r_receive(self, filename):
        """ Function which receives the data from Perseids

            - Receive PUT from Perseids
            - Check if content exist
            - Update/Create content
            - Open Pull Request
            - Return PR link to Perseids

        :param path: Path for the file
        :return:
        """
        content = request.files['content']
        author = request.args.get("author", None)
        if not author:
            author = self.default_author
        else:
            author = author.split("/")
            if len(author) < 2:
                author.append(self.default_author.email)
            author = Author(*author)
        date = request.args.get("date", datetime.datetime.now().date().isoformat())
        logs = request.args.get("logs", "{} updated {}".format(author, filename))
        secure_sha = request.args.get("sha")

        if not content:
            resp = jsonify({"error": "Content is missing"})
            resp.status_code = 300
            return resp

        file = File(
            path=filename,
            content=content,
            author=author,
            date=date,
            logs=logs
        )

        if not secure_sha or secure_sha != secure_sha:
            resp = jsonify({"error": "Hash does not correspond with content"})
            resp.status_code = 300
            return resp

        _get = self.get(file)
        if _get.status_code not in (200, 404):
            data = json.loads(_get.data.decode("utf-8"))
            resp = jsonify({
                "status": "error",
                "message": data["message"]
            })
            resp.status_code = _get.status_code
            return resp

        file_exists = _get.status_code == 200
        if file_exists:
            file_commit = self.update(file)
        else:
            # We create
            file_commit = self.put(file)

        return jsonify(file.dict())
