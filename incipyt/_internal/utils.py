from string import Formatter


def sanitizer_package(key, value):
    return value.replace("-", "_") if key == "NAME" else value


def sanitizer_project(key, value):
    return value.replace("_", "-") if key == "NAME" else value


class Requires:
    def __init__(self, template, sanitizer=None):
        self._sanitizer = sanitizer
        self._template = template

    def __call__(self, environment):
        return self._template.format(
            **{
                key: (
                    self._sanitizer(key, environment.pull(key))
                    if self._sanitizer
                    else environment.pull(key)
                )
                for _, key, _, _ in Formatter().parse(self._template)
                if key is not None
            }
        )


class MultipleValues:
    def __init__(self, head, tail):
        self._values = (
            [head] + tail._values if isinstance(tail, MultipleValues) else [head, tail]
        )

    def __call__(self, environment):
        candidates = [
            value(environment) if callable(value) else value for value in self._values
        ]
        raise NotImplementedError(
            f"Select candidates in {candidates} is not implemented"
        )


def append(config, key, value):
    if key in config:
        if config[key] != value:
            config[key] = MultipleValues(value, config[key])
    else:
        config[key] = value
