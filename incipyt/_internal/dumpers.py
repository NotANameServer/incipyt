import collections
import collections.abc
import configparser
import pathlib

import toml

from incipyt._internal import templates
from incipyt._internal import utils


class BaseDumper(type(pathlib.Path())):
    def __new__(cls, path, sanitizer=None):
        # As pathlib runs some magic in __new__ to instanciate a Path subclass
        # that matches the current platform, special precautions must be taken
        # when subclassing it
        self = super().__new__(cls, path)
        self._sanitizer = sanitizer
        self._root = None
        return self

    def commit(self, root, environment):
        self._environment = environment
        self._root = root

        path = self.substitute_path()
        if path.exists():
            raise RuntimeError(f"File {path} already exists.")

    def mkdir_in(self):
        self.substitute_path().parent.mkdir(parents=True, exist_ok=True)

    def substitute_path(self):
        context = templates.RenderContext(self._environment)
        path = str(self._root / self)
        return pathlib.Path(context.render_string(path))


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
        with self.substitute_path().open("w+") as file:
            config_cfg.write(file)


class Jinja(BaseDumper):
    def dump_in(self, template):
        context = templates.RenderContext(self._environment)
        with self.substitute_path().open("w+") as file:
            file.write(context.render_template(template))


class Requirement(BaseDumper):
    def dump_in(self, config):
        with self.substitute_path().open("w+") as file:
            file.write("\n".join(config[None]))


class Toml(BaseDumper):
    def dump_in(self, config):
        with self.substitute_path().open("w+") as file:
            toml.dump(config, file)
