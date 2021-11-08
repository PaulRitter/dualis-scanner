from setuptools import setup, find_packages


def get_version():
    with open("VERSION.txt") as ver_file:
        version_str = ver_file.readline().rstrip()
    return version_str


def get_install_requires():
    with open('requirements.txt') as reqs_file:
        reqs = [line.rstrip() for line in reqs_file.readlines()]
    return reqs


setup(
    name="dualis-scanner-worker",
    version=get_version(),
    packages=find_packages(".", exclude=["tests"]),
    entry_points={"console_scripts": ["dualis-scanner-worker=worker:main"]},
    install_requires=get_install_requires()
)