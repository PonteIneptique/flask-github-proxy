from flask import Flask, jsonify, request
import base64


def make_client(gitid, gitsec, route_fail=None):
    github_api = Flask("app")
    github_api.secret_id = gitsec
    github_api.client_id = gitid
    github_api.route_fail = route_fail
    if not route_fail:
        github_api.route_fail = {}

    def check_secret(response):
        if request.args.get("client_id") != github_api.client_id \
                or request.args.get("client_secret") != github_api.secret_id:
            response = jsonify(
                {
                    "message": "Bad credentials",
                    "documentation_url": "https://developer.github.com/v3"
                }
            )
            response.status_code = 401
        return response

    @github_api.route("/repos/<owner>/<repo>/git/refs", method="POST")
    def make_ref(owner, repo):
        if request.url.split("?")[0] in github_api.route_fail.keys():
            resp = jsonify({
                    "message": "Not Found",
                    "documentation_url": "https://developer.github.com/v3"
                }
            )
            resp.status_code = 404
            return resp

        data = request.data
        return jsonify({
          "ref": "refs/heads/featureA",
          "url": "https://api.github.com/repos/octocat/Hello-World/git/refs/heads/featureA",
          "object": {
            "type": "commit",
            "sha": "aa218f56b14c9653891f9e74264a383fa43fefbd",
            "url": "https://api.github.com/repos/octocat/Hello-World/git/commits/aa218f56b14c9653891f9e74264a383fa43fefbd"
          }
        })

    @github_api.route("/repos/<owner>/<repo>/contents/<path:file>", methods=["POST"])
    def put_file(owner, repo, file):
        resp = jsonify({
                "message": "Not Found",
                "documentation_url": "https://developer.github.com/v3"
            }
        )
        resp.status_code = 404
        return resp

    @github_api.route("/repos/<owner>/<repo>/contents/<path:file>", methods=["PUT"])
    def update_file(owner, repo, file):
        if request.url.split("?")[0] in github_api.route_fail.keys():
            resp = jsonify({
                    "message": "Not Found",
                    "documentation_url": "https://developer.github.com/v3"
                }
            )
            resp.status_code = 404
        else:
            data = request.data
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
                "git_url": "https://api.github.com/repos/{owner}/{repo}/git/blobs/95b966ae1c166bd92f8ae7d1c313e738c731dfc3",
                "download_url": "https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}".format(
                    owner=owner, repo=repo, branch=data["branch"], path=file
                ),
                "type": "file",
                "_links": {
                  "self": "https://github.com/octokit/{owner}/{repo}/{branch}/{path}".format(
                     owner=owner, repo=repo, branch=data["branch"], path=file
                   ),
                  "git": "https://api.github.com/repos/{owner}/{repo}/git/blobs/95b966ae1c166bd92f8ae7d1c313e738c731dfc3",
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
                  "email": data["author"]["mail"]
                },
                "message": "my commit message",
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
        return resp

    @github_api.route("/repos/<owner>/<repo>/contents/<path:file>", methods=["GET"])
    def check_file(owner, repo, file):
        if request.url.split("?")[0] in github_api.route_fail.keys():
            resp = jsonify({
                    "message": "Not Found",
                    "documentation_url": "https://developer.github.com/v3"
                }
            )
            resp.status_code = 404
            return resp
        sha = "123456"
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

    return github_api
