from setuptools import setup, find_packages

setup(
    name='nemo_arethusa_plugin',
    version="0.0.1",
    packages=find_packages(exclude=["examples", "tests"]),
    url='https://github.com/alpheios/nemo_arethusa_plugin',
    license='GNU GPL',
    author='Thibault Clerice',
    author_email='leponteineptique@gmail.com',
    description='Plugin for Capitains Nemo to load Arethusa on passage page',
    test_suite="tests",
    install_requires=[
        "flask_nemo>=1.0.0a"
    ],
    tests_require=[
        "capitains_nautilus>=0.0.5"
    ],
    include_package_data=True,
    zip_safe=False
)
