from string import Formatter

import collections.abc
import configparser
import pathlib
import toml


class BaseDumper(type(pathlib.Path())):
    @classmethod
    def make(cls, path, sanitizer=None):
        self = cls(path)
        self._sanitizer = sanitizer
        self._root = None

        return self

    def commit(self, root, environment):
        self._environment = environment
        self._root = root

        if self.substitute_path().exists():
            raise RuntimeError(f"File {self} already exists.")

    def mkdir_in(self):
        self.substitute_path().parent.mkdir(parents=True, exist_ok=True)

    def substitute_path(self):
        template_path = str(self._root.joinpath(self))
        template_keys = [item[1] for item in Formatter().parse(template_path)]

        keys = self._environment.pull_keys(template_keys, self._sanitizer)
        return pathlib.Path(template_path.format(**keys))


class CfgIni(BaseDumper):
    def dump_in(self, config):
        for section in config.values():
            for key, value in section.items():
                if isinstance(value, str):
                    continue
                elif isinstance(value, collections.abc.Sequence):
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
        with self.substitute_path().open("w+") as file:
            file.write(self._environment.render(template))


class Requirement(BaseDumper):
    def dump_in(self, config):
        with self.substitute_path().open("w+") as file:
            file.write("\n".join(config[None]))


class Toml(BaseDumper):
    def dump_in(self, config):
        with self.substitute_path().open("w+") as file:
            toml.dump(config, file)
