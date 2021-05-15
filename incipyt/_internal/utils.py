import collections.abc
from string import Formatter

import click


class Requires:
    def __init__(self, template, confirmed=False, sanitizer=None, **kwargs):
        self._confirmed = confirmed
        self._sanitizer = sanitizer
        self._template = template
        self._kwargs = kwargs

    def __str__(self):
        return f"f'{self._template}'"

    def __call__(self, environment):
        for _, key, _, _ in Formatter().parse(self._template):
            if key not in self._kwargs:
                continue

            environment.push(key, self._kwargs[key], confirmed=self._confirmed)

        args = {
            key: (
                self._sanitizer(key, environment.pull(key))
                if self._sanitizer
                else environment.pull(key)
            )
            for _, key, _, _ in Formatter().parse(self._template)
            if key is not None
        }
        if any(not v for v in args.values()):
            return None

        return self._template.format(**args)


class MultipleValues:
    def __init__(self, head, tail):
        self._values = (
            [head] + tail._values if isinstance(tail, MultipleValues) else [head, tail]
        )

    def __call__(self, environment):
        return click.prompt(
            "Conflicting configuration, choose between",
            type=click.Choice(
                [
                    value(environment) if callable(value) else value
                    for value in self._values
                ]
            ),
        )


def append_unique(config, value):
    assert isinstance(config, collections.abc.MutableSequence)

    if value not in config:
        config.append(value)


def set_item(config, key, value):
    assert isinstance(config, collections.abc.MutableMapping)

    if key in config:
        if config[key] != value:
            config[key] = MultipleValues(value, config[key])
    else:
        config[key] = value


def set_items(config, raw_config, transformer=None):
    assert isinstance(config, collections.abc.MutableMapping)
    assert isinstance(raw_config, collections.abc.Mapping)

    for key, value in raw_config.items():
        if isinstance(value, collections.abc.Mapping):
            if key not in config:
                config[key] = {}
            set_items(config[key], value, transformer=transformer)
        else:
            set_item(config, key, transformer(value) if transformer else value)
