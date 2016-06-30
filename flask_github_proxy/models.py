import base64
from hashlib import sha256
from flask import jsonify


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


class ProxyError(object):
    def __init__(self, code, message):
        self.code = code
        self.message = message

    def response(self):
        resp = jsonify({
            "status": "error",
            "message": self.message
        })
        resp.status_code = self.code
        return resp


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
        self.posted = False
        self.branch = None

    @property
    def path(self):
        return self.__path__

    @property
    def content(self):
        return base64.decodebytes(self.__content__.encode("utf-8"))

    @property
    def author(self):
        return self.__author__

    @property
    def date(self):
        return self.__date__

    @property
    def logs(self):
        return self.__logs__

    @property
    def sha(self):
        return sha256(self.base64).hexdigest()

    def dict(self):
        params = {
            prop: getattr(self, prop)
            for prop in [
                "logs", "date", "author", "sha", "path"
            ]
        }
        params["author"] = params["author"].dict()
        return params

    @property
    def base64(self):
        return self.__content__
