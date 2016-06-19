from flask_github import GitHub
from flask import Flask, Blueprint, request, jsonify
from tests.github import github_api
from copy import deepcopy
from hashlib import sha256
import datetime


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
        return params


class GithubProxy(GitHub):
    """ Provides routes to push files to github and open pull request as a service

    :param path: URI Prefix (Has to start with "/")
    :param source_repo:
    :param target_repo:
    :param app:

    """

    URLS = [
        ("/push/<path:filename>", "r_receive", ["POST"])
    ]

    def __init__(self, prefix, source_repo, target_repo, secret, app=None, default_author="Anonymous"):
        self.__blueprint__ = None
        self.__prefix__ = prefix
        self.__name__ = prefix.replace("/", "_").replace(".", "_")
        self.__source_repo__ = source_repo
        self.__target_repo__ = target_repo
        self.__secret__ = secret
        self.__urls__ = deepcopy(type(self).URLS)
        self.__default_author__ = default_author

        if app is not None:
            self.app = app
            self.init_app(self.app)
        else:
            self.app = None

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
        super(GithubProxy, self).init_app(app)
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
            print(url)
        self.app = self.app.register_blueprint(self.blueprint)

        return self.blueprint

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
        author = request.args.get("author", self.default_author)
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

        return jsonify(file.dict())
