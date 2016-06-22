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
        resp = jsonify({
                "message": "Not Found",
                "documentation_url": "https://developer.github.com/v3"
            }
        )
        resp.status_code = 404
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
            "html_url": "https://github.com/octokit/{owner}/{repo}/master/{path}".format(
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
