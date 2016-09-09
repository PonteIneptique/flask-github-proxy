from flask import Flask, jsonify, request
import base64
import json
from collections import defaultdict


def make_client(token, route_fail=None):
    github_api = Flask("app")
    github_api.token = token
    github_api.route_fail = route_fail
    github_api.sha_origin = "123456"
    github_api.new_sha = "abcdef"
    github_api.pr_number = 9
    github_api.exist_file = defaultdict(lambda: False)
    if not route_fail:
        github_api.route_fail = {}

    def check_secret(response):
        if request.headers["Authorization"] != "token %s" % github_api.token:
            response = jsonify(
                {
                    "message": "Bad credentials",
                    "documentation_url": "https://developer.github.com/v3"
                }
            )
            response.status_code = 401
        return response

    @github_api.route("/repos/<owner>/<repo>/git/refs", methods=["POST"])
    def make_ref(owner, repo):
        if request.url.split("?")[0] in github_api.route_fail.keys():
            resp = jsonify({
                    "message": "Not Found",
                    "documentation_url": "https://developer.github.com/v3"
                }
            )
            resp.status_code = 404
            return resp
        sha = github_api.sha_origin
        data = json.loads(request.data.decode("utf-8"))
        branch = "/".join(data["ref"].split("/")[3:])
        resp = jsonify({
          "ref": data["ref"],
          "url": "https://api.github.com/repos/{owner}/{repo}/git/refs/heads/{branch}".format(
            owner=owner, repo=repo, branch=branch
          ),
          "object": {
            "type": "commit",
            "sha": sha,
            "url": "https://api.github.com/repos/{owner}/{repo}/git/commits/{sha}".format(
                owner=owner, repo=repo, sha=sha
            )
          }
        })
        resp.status_code = 201
        return resp

    @github_api.route("/repos/<owner>/<repo>/git/refs/heads/<branch>", methods=["GET"])
    def get_ref(owner, repo, branch):
        r = request.url.split("?")[0]
        if r in github_api.route_fail.keys():

            if github_api.route_fail[r] is True:
                # Used when we want to make a branch creation
                resp = jsonify({
                        "message": "Not Found",
                        "documentation_url": "https://developer.github.com/v3"
                    }
                )
                resp.status_code = 404
                return resp
            else:
                # Used to detect failing on  GitHub API side

                resp = jsonify({
                    "message": "Bad credentials",
                    "documentation_url": "https://developer.github.com/v3"
                })
                resp.status_code = 401
                return resp

        sha = github_api.sha_origin
        return jsonify({
          "ref": "refs/heads/{branch}".format(branch=branch),
          "url": "https://api.github.com/repos/{owner}/{repo}/git/refs/heads/{branch}".format(
            owner=owner, repo=repo, branch=branch
          ),
          "object": {
            "type": "commit",
            "sha": sha,
            "url": "https://api.github.com/repos/{owner}/{repo}/git/commits/{sha}".format(
                owner=owner, repo=repo, sha=sha
            )
          }
        })

    @github_api.route("/repos/<owner>/<repo>/contents/<path:file>", methods=["POST"])
    def put_file(owner, repo, file):
        if request.url.split("?")[0] in github_api.route_fail.keys():
            resp = jsonify({
                    "message": "Not Found",
                    "documentation_url": "https://developer.github.com/v3"
                }
            )
            resp.status_code = 404

    @github_api.route("/repos/<owner>/<repo>/contents/<path:file>", methods=["PUT"])
    def update_file(owner, repo, file):
        if request.url.split("?")[0] in github_api.route_fail.keys():
            resp = jsonify({
                    "message": "Not Found",
                    "documentation_url": "https://developer.github.com/v3"
                }
            )
            resp.status_code = 404
        elif github_api.exist_file[file] is True:
            data = json.loads(request.data.decode("utf-8"))
            resp = {
                "commit": {
                    "author": {
                        "date": "2014-11-07T22:01:45Z",
                        "name": data["author"]["name"],
                         "email": data["author"]["email"]
                    },
                    "committer": {
                        "date": "2014-11-07T22:01:45Z",
                        "email": "schacon@gmail.com",
                        "name": "Scott Chacon"
                    },
                    "html_url": "https://github.com/{owner}/{repo}/git/commit/7638417db6d59f3c431d3e1f261cc637155684cd".format(
                        owner=owner, repo=repo
                    ),
                    "message": data["message"],
                    "parents": [
                        {
                            "html_url": "https://github.com/{owner}/{repo}/git/commit/{oldsha}".format(
                                owner=owner, repo=repo, oldsha=data["sha"]
                            ),
                            "sha": "1acc419d4d6a9ce985db7be48c6349a0475975b5",
                            "url": "https://api.github.com/repos/{owner}/{repo}/git/commits/{oldsha}".format(
                                owner=owner, repo=repo, oldsha=data["sha"]
                            )
                        }
                    ],
                    "sha": "7638417db6d59f3c431d3e1f261cc637155684cd",
                    "tree": {
                        "sha": "691272480426f78a0138979dd3ce63b77f706feb",
                        "url": "https://api.github.com/repos/{owner}/{repo}/git/trees/691272480426f78a0138979dd3ce63b77f706feb".format(
                            owner=owner, repo=repo
                        )
                    },
                    "url": "https://api.github.com/repos/{owner}/{repo}/git/commits/7638417db6d59f3c431d3e1f261cc637155684cd".format(
                        owner=owner, repo=repo
                    )
                },
                "content": {
                    "_links": {
                        "git": "https://api.github.com/repos/{owner}/{repo}/git/blobs/{sha}".format(
                            owner=owner, repo=repo, sha=github_api.new_sha
                        ),
                        "html": "https://github.com/{owner}/{repo}/blob/{branch}/{path}".format(
                            owner=owner, repo=repo, path=file, branch=data["branch"]
                        ),
                        "self": "https://api.github.com/repos/{owner}/{repo}/contents/{path}".format(
                            owner=owner, repo=repo, path=file
                        )
                    },
                    "download_url": "https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}".format(
                        owner=owner, repo=repo, path=file, branch=data["branch"]
                    ),
                    "git_url": "https://api.github.com/repos/{owner}/{repo}/git/blobs/{sha}".format(
                        owner=owner, repo=repo, sha=github_api.new_sha
                    ),
                    "html_url": "https://github.com/{owner}/{repo}/blob/{branch}/{path}".format(
                        owner=owner, repo=repo, path=file, branch=data["branch"]
                    ),
                    "name": file.split("/")[-1],
                    "path": file,
                    "sha": github_api.new_sha,
                    "size": 9,
                    "type": "file",
                    "url": "https://api.github.com/repos/{owner}/{repo}/contents/{path}".format(
                        owner=owner, repo=repo, path=file
                    )
                }
            }
            resp = jsonify(data)
            resp.status_code = 200
        else:
            data = json.loads(request.data.decode("utf-8"))
            resp = jsonify({
              "content": {
                "name": file.split("/")[-1],
                "path": file,
                "sha": "95b966ae1c166bd92f8ae7d1c313e738c731dfc3",
                "size": 9,
                "url": "https://github.com/{owner}/{repo}/{branch}/{path}".format(
                    owner=owner, repo=repo, branch=data["branch"], path=file
                ),
                "html_url": "https://github.com/{owner}/{repo}/blob/{branch}/{path}".format(
                    owner=owner, repo=repo, branch=data["branch"], path=file
                ),
                "git_url": "https://api.github.com/repos/{owner}/{repo}/git/blobs/95b966ae1c166bd92f8ae7d1c313e738c731dfc3".format(
                    owner=owner, repo=repo
                ),
                "download_url": "https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}".format(
                    owner=owner, repo=repo, branch=data["branch"], path=file
                ),
                "type": "file",
                "_links": {
                  "self": "https://github.com/octokit/{owner}/{repo}/{branch}/{path}".format(
                     owner=owner, repo=repo, branch=data["branch"], path=file
                   ),
                  "git": "https://api.github.com/repos/{owner}/{repo}/git/blobs/95b966ae1c166bd92f8ae7d1c313e738c731dfc3".format(
                        owner=owner, repo=repo
                    ),
                  "html": "https://github.com/{owner}/{repo}/blob/{branch}/{path}".format(
                        owner=owner, repo=repo, branch=data["branch"], path=file
                    )
                }
              },
              "commit": {
                "sha": "7638417db6d59f3c431d3e1f261cc637155684cd",
                "url": "https://api.github.com/repos/{owner}/{repo}/git/commits/7638417db6d59f3c431d3e1f261cc637155684cd".format(
                    owner=owner, repo=repo
                ),
                "html_url": "https://github.com/{owner}/{repo}/git/commit/7638417db6d59f3c431d3e1f261cc637155684cd".format(
                    owner=owner, repo=repo
                ),
                "author": {
                  "date": "2014-11-07T22:01:45Z",
                  "name": data["author"]["name"],
                  "email": data["author"]["email"]
                },
                "message": data["message"],
                "tree": {
                  "url": "https://api.github.com/repos/{owner}/{repo}/git/trees/691272480426f78a0138979dd3ce63b77f706feb".format(
                    owner=owner, repo=repo
                ),
                  "sha": "691272480426f78a0138979dd3ce63b77f706feb"
                },
                "parents": [
                  {
                    "url": "https://api.github.com/repos/{owner}/{repo}/git/commits/1acc419d4d6a9ce985db7be48c6349a0475975b5".format(
                        owner=owner, repo=repo
                    ),
                    "html_url": "https://github.com/{owner}/{repo}/git/commit/1acc419d4d6a9ce985db7be48c6349a0475975b5".format(
                        owner=owner, repo=repo
                    ),
                    "sha": "1acc419d4d6a9ce985db7be48c6349a0475975b5"
                  }
                ]
              }
            })
            resp.status_code = 201
        return resp

    @github_api.route("/repos/<owner>/<repo>/contents/<path:file>", methods=["GET"])
    def check_file(owner, repo, file):
        if request.url.split("?")[0] in github_api.route_fail.keys() or github_api.exist_file[file] is False:
            resp = jsonify({
                    "message": "Not Found",
                    "documentation_url": "https://developer.github.com/v3"
                }
            )
            resp.status_code = 404
            return resp
        sha = github_api.sha_origin
        model = {
            "type": "file",
            "encoding": "base64",
            "size": 5362,
            "name": file.split("/")[-1],
            "path": file,
            "content": base64.b64encode(b"encoded content ...").decode('utf-8'),
            "sha": sha,
            "url": "https://api.github.com/repos/{owner}/{repo}/contents/{path}".format(
                owner=owner, repo=repo, path=file
            ),
            "git_url": "https://api.github.com/repos/{owner}/{repo}/git/blobs/{sha}".format(
                owner=owner, repo=repo, sha=sha
            ),
            "html_url": "https://github.com/{owner}/{repo}/master/{path}".format(
                owner=owner, repo=repo, path=file
            ),
            "download_url": "https://raw.githubusercontent.com/{owner}/{repo}/master/{path}".format(
                owner=owner, repo=repo, path=file
            ),
            "_links": {
                "git": "https://api.github.com/repos/{owner}/{repo}/git/blobs/{sha}".format(
                    owner=owner, repo=repo, sha=sha
                ),
                "self": "https://api.github.com/repos/{owner}/{repo}/contents/{path}".format(
                    owner=owner, repo=repo, path=file
                ),
                    "html": "https://github.com/{owner}/{repo}/blob/master/{path}".format(
                    owner=owner, repo=repo, path=file
                )
            }
        }
        return check_secret(jsonify(model))

    @github_api.route("/repos/<owner>/<repo>/pulls", methods=["POST"])
    def make_pr(owner, repo):
        pr_number = github_api.pr_number
        if request.url.split("?")[0] in github_api.route_fail.keys():
            resp = jsonify({
                    "message": "Not Found",
                    "documentation_url": "https://developer.github.com/v3"
                }
            )
            resp.status_code = 404
            return resp
        data = json.loads(request.data.decode("utf-8"))
        reply = jsonify({
          "id": 1,
          "url": "https://api.github.com/repos/{owner}/{repo}/pulls/{nb}".format(
              owner=owner, repo=repo, nb=pr_number
          ),
          "html_url": "https://github.com/{owner}/{repo}/pull/{nb}".format(
              owner=owner, repo=repo, nb=pr_number
          ),
          "title": data["title"],
          "body": data["body"],
        })
        reply.status_code = 201
        return reply

    return github_api
