import pathlib
import urllib


def package(key, value):
    return value.replace("-", "_") if key == "NAME" else value


def project(key, value):
    return value.replace("_", "-") if key == "NAME" else value


def url(key, value):
    parts = urllib.parse.urlparse(value)
    parts._replace(path=str(pathlib.Path(parts.path)))
    return parts.geturl()


def version(key, value):
    if any(not num.isdigit() for num in value.split(".")):
        raise ValueError(f"{value} is not a valid version number")

    return value
