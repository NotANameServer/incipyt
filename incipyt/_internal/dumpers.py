import collections
import collections.abc
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
        unfolded_dict = False
        while not unfolded_dict:
            unfolded_dict = True
            for section_key in list(config.keys()):
                for key in list(config[section_key].keys()):
                    if not isinstance(
                        config[section_key][key], collections.abc.Mapping
                    ):
                        continue
                    new_section_key = f"{section_key}.{key}"
                    if new_section_key in config:
                        raise RuntimeError(
                            f"Bad cfg formation for section {new_section_key} of {self._path}"
                        )
                    config[new_section_key] = config[section_key][key]
                    del config[section_key][key]
                    unfolded_dict = False
        for section in config.values():
            for key, value in section.items():
                if utils.is_nonstring_sequence(value):
                    section[key] = "\n".join([""] + value)

        config_cfg = configparser.ConfigParser()
        config_cfg.read_dict(config)
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
