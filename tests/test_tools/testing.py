import io
import contextlib
import pathlib
import re
import sys

import typing as t

from click import termui, testing, types


from incipyt import project


def diff_files(dircmp):
    result = {str(pathlib.Path(dircmp.left) / f) for f in dircmp.diff_files}
    for sd in dircmp.subdirs.values():
        result |= diff_files(sd)
    return {
        path
        for path in result
        if not any(
            re.match(pattern, path) for pattern in [r".*/\.env/.*", r".*/dist/.*"]
        )
    }


class IncipytRunner(testing.CliRunner):
    def __init__(
        self,
        input_mapping: t.Mapping[str, str] = None,
        default_mapping: t.Mapping[str, str] = None,
        charset: str = "utf-8",
        env: t.Optional[t.Mapping[str, t.Optional[str]]] = None,
    ) -> None:
        super().__init__(charset=charset, env=env, echo_stdin=False, mix_stderr=True)
        self._input_mapping = {
            r"Audience python version": "3.7",
            r"Author name": "John Doe",
            r"Author email": "john.doe@example.com",
            r"Package version": "",
            r"Project name": "",
            r"Summary description": "My summary",
        }
        self._default_mapping = {
            r"Package version": r"0.0.0",
        }
        if input_mapping is not None:
            self._input_mapping.update(input_mapping)
        if default_mapping is not None:
            self._default_mapping.update(default_mapping)
        self._last_value = None

    @contextlib.contextmanager
    def isolation(
        self,
        input: t.Optional[t.Union[str, bytes, t.IO]] = None,  # noqa: A002
        env: t.Optional[t.Mapping[str, t.Optional[str]]] = None,
        color: bool = False,
    ) -> t.Iterator[t.Tuple[io.BytesIO, t.Optional[io.BytesIO]]]:
        assert input is None, "IncipytRunner.isolation input parameter disabled"
        assert env is None, "IncipytRunner.isolation env parameter disabled"

        old_stdout = sys.stdout
        old_stderr = sys.stderr

        sys.stderr = sys.stdout = testing._NamedTextIOWrapper(
            io.BytesIO(), encoding=self.charset, name="<stdout>", mode="w"
        )

        def visible_input(prompt: t.Optional[str] = None) -> str:
            assert self._last_value is not None, "Empty prompt"
            val = self._last_value
            self._last_value = None
            sys.stdout.write(prompt or "")
            sys.stdout.write(f"{val}\n")
            sys.stdout.flush()
            return val

        def hidden_input(prompt: t.Optional[str] = None) -> str:
            assert self._last_value is not None, "Empty prompt"
            val = self._last_value
            self._last_value = None
            sys.stdout.write(f"{prompt or ''}\n")
            sys.stdout.flush()
            return val

        def _build_prompt(
            text: str,
            suffix: str,
            show_default: bool = False,
            default: t.Optional[t.Any] = None,
            show_choices: bool = True,
            type: t.Optional[types.ParamType] = None,  # noqa: A002
        ) -> str:
            prompt = text
            assert prompt is not None, "Empty prompt"
            values = [
                value
                for pattern, value in self._input_mapping.items()
                if re.match(pattern, prompt)
            ]
            if type is not None and show_choices and isinstance(type, types.Choice):
                prompt += f" ({', '.join(map(str, type.choices))})"
            if default is not None and show_default:
                default_prompt = termui._format_default(default)
                default_paterns = [
                    pattern_value
                    for pattern, pattern_value in self._default_mapping.items()
                    if re.match(pattern, prompt)
                ]
                prompt = f"{prompt} [{default_prompt}]"
                assert (
                    len(default_paterns) <= 1
                ), f"{{{prompt}}} doesn't match at most one input pattern"
                if len(default_paterns) == 1:
                    assert re.match(
                        default_paterns[0], default_prompt
                    ), f"{{{prompt}}} default value doesn't match the expected pattern [{default_paterns[0]}]"
            assert (
                len(values) == 1
            ), f"{{{prompt}}} doesn't match one and only one input patterns"
            self._last_value = values[0]
            return f"{prompt}{suffix}"

        old_visible_prompt_func = termui.visible_prompt_func
        old_hidden_prompt_func = termui.hidden_prompt_func
        old__build_prompt = termui._build_prompt
        termui.visible_prompt_func = visible_input
        termui.hidden_prompt_func = hidden_input
        termui._build_prompt = _build_prompt

        project.environ.clear()
        project.structure.clear()

        yield (sys.stdout.buffer, None)

        project.environ.clear()
        project.structure.clear()

        sys.stdout = old_stdout
        sys.stderr = old_stderr
        termui.visible_prompt_func = old_visible_prompt_func
        termui.hidden_prompt_func = old_hidden_prompt_func
        termui._build_prompt = old__build_prompt
