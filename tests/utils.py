import io

from incipyt._internal.utils import is_nonstring_sequence


def mock_stdin(monkeypatch, inputs):
    if not is_nonstring_sequence(inputs):
        inputs = (inputs,)
    monkeypatch.setattr("sys.stdin", io.StringIO("".join(f"{v}\n" for v in inputs)))
