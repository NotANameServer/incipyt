import os
import pathlib
import urllib


def package(key, value):
    return value.replace("-", "_") if key == "NAME" else value


def project(key, value):
    return value.replace("_", "-") if key == "NAME" else value


def url(key, value):
    parts = urllib.parse.urlparse(value)
    parts._replace(path=os.fspath(pathlib.Path(parts.path)))
    return parts.geturl()


def version(key, value):
    return value
