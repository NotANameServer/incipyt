import collections
import collections.abc
import configparser
import pathlib

import toml

from incipyt._internal import templates, utils


class BaseDumper:
    def __init__(self, path, sanitizer=None):
        self._path = pathlib.Path(path)
        self._root = None
        self._sanitizer = sanitizer

    def commit(self, root):
        self._root = root

        path = self.format_path()
        if path.exists():
            raise RuntimeError(f"File {path} already exists.")

    def mkdir(self):
        self.format_path().parent.mkdir(parents=True, exist_ok=True)

    def open(self, mode="w+", **kwargs):  # noqa: A003
        return self.format_path().open(mode=mode, **kwargs)

    def format_path(self):
        if self._root is None:
            raise RuntimeError("Root is missing.")

        return pathlib.Path(
            templates.FormatterEnviron(sanitizer=self._sanitizer).format(
                str(self._root / self._path)
            )
        )

    def __hash__(self):
        return hash(self._path)

    def __repr__(self):
        return utils.make_repr(
            self,
            root=self._root,
            path=self._path,
            sanitizer=self._sanitizer,
        )

    def __eq__(self, other):
        return utils.attrs_eq(self, other, "_path")


class CfgIni(BaseDumper):
    def dump_in(self, config):
        for section in config.values():
            for key, value in section.items():
                if utils.is_nonstring_sequence(value):
                    section[key] = "\n".join([""] + value)
                elif isinstance(value, collections.abc.Mapping):
                    section[key] = "\n".join(
                        [""] + [f"{k} = {v}" for k, v in value.items()]
                    )
        config_cfg = configparser.ConfigParser()
        config_cfg.read_dict(config)
        with self.open() as file:
            config_cfg.write(file)


class Raw(BaseDumper):
    def dump_in(self, config):
        with self.open() as file:
            file.write(config[None])


class Requirement(BaseDumper):
    def dump_in(self, config):
        with self.open() as file:
            file.write("\n".join(config[None]))


class Toml(BaseDumper):
    def dump_in(self, config):
        with self.open() as file:
            toml.dump(config, file)
