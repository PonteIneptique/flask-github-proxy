from flask import Flask, jsonify, request

github_api = Flask("app")
github_api.secret_id = "secret-id"
github_api.client_id = "client-id"


def check_secret(response):
    if request.get("client_id") != github_api.client_id \
            or request.get("client_secret") != github_api.secret_id:
        response = jsonify(
            {
                "message": "Bad credentials",
                "documentation_url": "https://developer.github.com/v3"
            }
        )
        response.status_code = 401
    return response


@github_api.route("/repos/<owner>/<repo>/contents/<path:file>")
def check_file(owner, repo, file):
    model = {
        "type": "file",
        "encoding": "base64",
        "size": 5362,
        "name": "README.md",
        "path": "README.md",
        "content": "encoded content ...",
        "sha": "3d21ec53a331a6f037a91c368710b99387d012c1",
        "url": "https://api.github.com/repos/octokit/octokit.rb/contents/README.md",
        "git_url": "https://api.github.com/repos/octokit/octokit.rb/git/blobs/3d21ec53a331a6f037a91c368710b99387d012c1",
        "html_url": "https://github.com/octokit/octokit.rb/blob/master/README.md",
        "download_url": "https://raw.githubusercontent.com/octokit/octokit.rb/master/README.md",
        "_links": {
            "git": "https://api.github.com/repos/octokit/octokit.rb/git/blobs/3d21ec53a331a6f037a91c368710b99387d012c1",
            "self": "https://api.github.com/repos/octokit/octokit.rb/contents/README.md",
            "html": "https://github.com/octokit/octokit.rb/blob/master/README.md"
        }
    }
    return check_secret(jsonify(model))
