import configparser
import os
import pathlib

from abc import ABC, abstractmethod

import toml

from incipyt._internal import templates, utils


class BaseDumper(ABC):
    def __init__(self, path, sanitizer=None):
        self._path = pathlib.Path(path)
        self._root = None
        self._sanitizer = sanitizer

    @abstractmethod
    def dump_in(self, config):
        raise NotImplementedError

    def commit(self, root):
        self._root = root

        path = self.format_path()
        if path.exists():
            raise FileExistsError(f"File {path} already exists.")

    def mkdir(self):
        self.format_path().parent.mkdir(parents=True, exist_ok=True)

    def open(self, mode="w+", **kwargs):  # noqa: A003
        return self.format_path().open(mode=mode, **kwargs)

    def format_path(self):
        if self._root is None:
            raise RuntimeError("Root is missing.")

        return pathlib.Path(
            templates.FormatterEnviron(sanitizer=self._sanitizer).format(
                os.fspath(self._root / self._path)
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
        config_cfg = configparser.ConfigParser()
        config_cfg.read_dict(utils.unfold_dict(utils.unfold_list(config)))
        with self.open() as file:
            config_cfg.write(file)


class TextFile(BaseDumper):
    def __init__(self, path, sep="\n", sanitizer=None):
        super().__init__(path, sanitizer)
        self._sep = sep

    def dump_in(self, config):
        with self.open() as file:
            file.write(self._sep.join(config) + self._sep)


class Toml(BaseDumper):
    def dump_in(self, config):
        with self.open() as file:
            toml.dump(config, file)
