.. image:: https://coveralls.io/repos/ponteineptique/flask-github-proxy/badge.svg?service=github
  :alt: Coverage Status
  :target: https://coveralls.io/github/ponteineptique/flask-github-proxy
.. image:: https://travis-ci.org/ponteineptique/flask-github-proxy.svg
  :alt: Build Status
  :target: https://travis-ci.org/ponteineptique/flask-github-proxy
.. image:: https://badge.fury.io/py/flask_github_proxy.svg
  :alt: PyPI version
  :target: http://badge.fury.io/py/flask_github_proxy
.. image:: https://readthedocs.org/projects/docs/badge/?version=latest
    :alt: Documentation
    :target: https://flask-github-proxy.readthedocs.io/en/latest/

What ?
######

Flask Github proxy is a flask extension to provide saving resources to GitHub. To use this service, you will need a github token (Generate token : https://github.com/settings/tokens )

Installation
############

To install it, simply do : :code:`pip3 install flask_github_proxy` or

.. code-block:: bash

    git clone https://github.com/ponteineptique/flask-github-proxy.git
    cd flask-github-proxy
    python3 setup.py install

Example
#######

.. code-block:: python
    :linenos:

    from flask import Flask
    from flask_github_proxy import GithubProxy
    from flask_github_proxy.models import Author
    
    app = Flask("name")
    proxy = GithubProxy(
        "/proxy",
        "ponteineptique/dummy1",
        "alpheios-project/dummy1",
        secret="something",
        token="Github Token",
        app=app,
        origin_branch="master",
        default_author=Author(
            "Github Proxy",
            "anonymous@github.com"
        )
    )
    app.run()

Funding and original development
################################

This python software has originally been developed in the context of the Syriaca_ Project, under the funding of NEH.

.. image:: ./_static/images/neh_logo.png
    :alt: NEH
    :target: http://www.neh.gov/

.. _Syriaca: http://www.syriaca.org/