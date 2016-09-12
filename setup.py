from setuptools import setup, find_packages

setup(
    name='flask_github_proxy',
    version="0.0.1",
    packages=find_packages(exclude=["examples", "tests"]),
    url='https://github.com/ponteineptique/flask-github-proxy',
    license='GNU GPL',
    author='Thibault Clerice',
    author_email='leponteineptique@gmail.com',
    description=""" Plugin to build services to push data from a website to github with PullRequests confirmation
    """,
    test_suite="tests",
    install_requires=[
        "Flask==0.11.1",
        "GitHub-Flask==3.1.2",
        "requests==2.10.0",
    ],
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Framework :: Flask"
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3.5",
        "Topic :: Documentation :: Sphinx",
        "Topic :: Internet :: Proxy Servers"

    ]
)
