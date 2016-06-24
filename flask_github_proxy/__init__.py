from flask import Blueprint, request, jsonify
from copy import deepcopy
import datetime
import json
from requests import request as make_request
from flask_github_proxy.models import Author, File, ProxyError


class GithubProxy(object):
    """ Provides routes to push files to github and open pull request as a service

    :param path: URI Prefix (Has to start with "/")
    :param origin:
    :param upstream:
    :param app:

    """

    URLS = [
        ("/push/<path:filename>", "r_receive", ["POST"])
    ]

    DEFAULT_AUTHOR = Author(
        "Github Proxy",
        "anonymous@github.com"
    )

    class DEFAULT_BRANCH:
        NO = -1
        AUTO_SHA = 0

    def __init__(self,
                 prefix, origin, upstream,
                 secret,
                 github_secret, github_id,
                 default_branch=None, origin_branch="master",
                 app=None, default_author=None):

        self.__blueprint__ = None
        self.__prefix__ = prefix
        self.__name__ = prefix.replace("/", "_").replace(".", "_")
        self.__origin__ = origin
        self.__upstream__ = upstream
        self.__secret__ = secret
        self.__urls__ = deepcopy(type(self).URLS)
        self.__default_author__ = default_author
        self.__default_branch__ = default_branch
        self.github_secret = github_secret
        self.github_id = github_id

        self.origin_branch = origin_branch
        if default_branch is None:
            self.__default_branch__ = GithubProxy.DEFAULT_BRANCH.NO

        self.github_api_url = "https://api.github.com"
        if not default_author:
            self.__default_author__ = GithubProxy.DEFAULT_AUTHOR

        if app is not None:
            self.app = app
            self.init_app(self.app)
        else:
            self.app = None

    def request(self, method, url, **kwargs):
        """ Unified method to make request to the Github API

        :param method: HTTP Method to use
        :param url: URL to reach
        :param kwargs: dictionary of arguments (params for URL parameters, data for post/put data)
        :return: Response
        """
        if "params" not in kwargs:
            kwargs["params"] = {}
        kwargs["params"]["client_id"] = self.github_id
        kwargs["params"]["client_secret"] = self.github_secret
        if "data" in kwargs:
            kwargs["data"] = json.dumps(kwargs["data"])
        return make_request(
            method,
            url,
            **kwargs
        )

    def default_branch(self, file):
        """ Decide the name of the default branch given the file and the configuration

        :param file: File with informations about it
        :return:
        """
        if isinstance(self.__default_branch__, str):
            return self.__default_branch__
        elif self.__default_branch__ == GithubProxy.DEFAULT_BRANCH.NO:
            return None
        else:
            return file.sha

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
    def origin(self):
        return self.__origin__

    @property
    def upstream(self):
        return self.__upstream__

    @property
    def default_author(self):
        return self.__default_author__

    @property
    def secret(self):
        return self.__secret__

    def init_app(self, app):
        """ Initialize the application and register the blueprint

        :param app:

        :return: Blueprint of the current nemo app
        :rtype: flask.Blueprint
        """
        self.app = app
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
        """ Create a new file on github

        :param file: File to create
        :return: File or ProxyError
        """
        data = self.request(
            "PUT",
            "{api}/repos/{origin}/contents/{path}".format(
                api=self.github_api_url,
                origin=self.origin,
                path=file.path
            ),
            data={
                "message": file.logs,
                "author": file.author.dict(),
                "content": file.base64(),
                "branch": file.branch
            }
        )

        if data.status_code == 201:
            file.pushed = True
            return file
        else:
            reply = json.loads(data.data.decode("utf-8"))
            return ProxyError(data.status_code, reply["message"])

    def get(self, file):
        """ Check on github if a file exists

        :param file: File to check status of
        :return: File with new information, including blob
        """
        data = self.request(
            "GET",
            "{api}/repos/{origin}/contents/{path}".format(
                api=self.github_api_url,
                origin=self.origin,
                path=file.path
            ),
            params={
                "ref": file.branch
            }
        )
        # We update the file blob because it exists and we need it for update
        if data.status_code == 200:
            data = json.loads(data.data.decode("utf-8"))
            file.blob = data["sha"]
        elif data.status_code == 404:
            pass
        else:
            data = json.loads(data.data.decode("utf-8"))
            return ProxyError(data.status_code, data["message"])
        return file

    def update(self, file):
        """ Make an update query on Github API for given file

        :param file: File to update, with its content
        :return: File with new information, including success
        """
        data = self.request(
            "POST",
            "{api}/repos/{origin}/contents/{path}".format(
                api=self.github_api_url,
                origin=self.origin,
                path=file.path
            ),
            data={
                "message": file.logs,
                "author": file.author.dict(),
                "content": file.base64(),
                "sha": file.blob,
                "branch": file.branch
            }
        )
        if data.status_code == 200:
            file.pushed = True
            return file
        else:
            reply = json.loads(data.data.decode("utf-8"))
            return ProxyError(data.status_code, reply["message"])

    def pull_request(self, file):
        """ Create a pull request

        :param file:
        :return:
        """
        data = self.request(
            "PUT",
            "{api}/repos/{upstream}/pulls".format(
                api=self.github_api_url,
                upstream=self.upstream,
                path=file.path
            ),
            data={
                "message": file.logs,
                "author": file.author.dict(),
                "head": "{}:{}".format(self.origin.split("/")[0], file.branch),
                "base": self.origin_branch
            }
        )

        if data.status_code == 200:
            file.pushed = True
            return file
        else:
            reply = json.loads(data.data.decode("utf-8"))
            return ProxyError(data.status_code, reply["message"])

    def get_ref(self, branch):
        """ Check if a reference exists

        :param branch: The branch to check if it exists
        :return: Sha of the branch if it exists, False if it does not exist, ProxyError if it went wrong
        """
        data = self.request(
            "GET",
            "{api}/repos/{origin}/git/refs/heads/{branch}".format(
                api=self.github_api_url,
                origin=self.origin,
                branch=branch
            )
        )
        if data.status_code == 200:
            data = json.loads(data.data.decode("utf-8"))
            if isinstance(data, list):
                # No addresses matches, we get search results which stars with {branch}
                return False
            #  Otherwise, we get one record
            return data["object"]["sha"]
        elif data.status_code == 404:
            return False
        else:
            data = json.loads(data.data.decode("utf-8"))
            return ProxyError(data.status_code, data["message"])

    def make_pull(self, file):
        """ Make a pull request based on the file

        :param file:
        :return:
        """
        data = self.request(
            "GET",
            "{api}/repos/{origin}/pulls".format(
                api=self.github_api_url,
                origin=self.origin
            ),
            data={
              "title": "[Proxy] {message}".format(message=file.logs),
              "body": "",
              "head": file.branch,
              "base": self.origin_branch
            }

        )
        if data.status_code == 201:
            data = json.loads(data.data.decode("utf-8"))
            if isinstance(data, list):
                # No addresses matches, we get search results which stars with {branch}
                return False
            #  Otherwise, we get one record
            return data["html_url"]
        elif data.status_code == 404:
            return False
        else:
            data = json.loads(data.data.decode("utf-8"))
            return ProxyError(data.status_code, data["message"])

    def make_ref(self, branch):
        """ Make a branch on github

        :param branch: Name of the branch to create
        :return: Sha of the branch or ProxyError
        """
        master_sha = self.get_ref(self.origin_branch)
        if not isinstance(master_sha, str):
            return ProxyError(
                404,
                "The default branch from which to checkout is either not available or does not exist"
            )

        data = self.request(
            "POST",
            "{api}/repos/{origin}/git/refs".format(
                api=self.github_api_url,
                origin=self.origin
            ),
            data={
              "ref": "refs/heads/{branch}".format(branch=branch),
              "sha": master_sha
            }
        )

        if data.status_code == 201:
            data = json.loads(data.data.decode("utf-8"))
            if isinstance(data, list):
                # No addresses matches, we get search results which stars with {branch}
                return False
            #  Otherwise, we get one record
            return data["object"]["sha"]
        else:
            answer = json.loads(data.data.decode("utf-8"))
            return ProxyError(data.status_code, answer["message"])

    def r_receive(self, filename):
        """ Function which receives the data from Perseids

            - Check the branch does not exist
            - Make the branch if needed
            - Receive PUT from Perseids
            - Check if content exist
            - Update/Create content
            - Open Pull Request
            - Return PR link to Perseids

        :param filename: Path for the file
        :return:
        """
        ###########################################
        # Retrieving data
        ###########################################
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

        # Content checking
        if not content:
            error = ProxyError(300, "Content is missing")
            return error.response()

        ###########################################
        # Setting up data
        ###########################################
        file = File(
            path=filename,
            content=content,
            author=author,
            date=date,
            logs=logs
        )
        file.branch = request.args.get("branch", self.default_branch(file))

        ###########################################
        # Checking data security
        ###########################################
        if not secure_sha or secure_sha != secure_sha:
            error = ProxyError(300, "Hash does not correspond with content")
            return error.response()

        ###########################################
        # Ensuring branch exists
        ###########################################
        branch_status = self.get_ref(file.branch)

        if isinstance(branch_status, ProxyError):  # If we have an error from github API
            return branch_status.response()
        elif not branch_status:  # If it does not exist
            # We create a branch
            branch_status = self.make_ref(file.branch)
            # If branch creation did not work
            if isinstance(branch_status, ProxyError):
                return branch_status.response()

        ###########################################
        # Pushing files
        ###########################################
        # Check if file exists
        # It feeds file.blob parameter, which tells us the sha of the file if it exists
        file = self.get(file)
        if isinstance(file, ProxyError):  # If we have an error from github API
            return file.response()

        # If it has a blob set up, it means we can update given file
        if file.blob:
            file = self.update(file)
        # Otherwrise, we create it
        else:
            file = self.put(file)
        if isinstance(file, ProxyError):
            return file.response()

        ###########################################
        # Making pull request
        ###########################################

        return jsonify(file.dict())
