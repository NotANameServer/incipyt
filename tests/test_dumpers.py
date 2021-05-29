from jinja2 import Template
from pytest import fixture, mark, raises

from incipyt.system import Environment
from incipyt._internal.dumpers import BaseDumper, CfgIni, Jinja, Requirement, Toml


@fixture
def env():
    return Environment(auto_confirm=True)


def test_format_path(env, tmp_path):
    dmp = BaseDumper("{first}/{second}.ext")
    env.push("first", "folder")
    env.push("second", "file")
    dmp.commit(tmp_path, env)
    assert dmp.substitute_path() == tmp_path / "folder" / "file.ext"


def test_mkdir(env, tmp_path):
    dmp = BaseDumper("folder/file")
    dmp.commit(tmp_path, env)
    dmp.mkdir_in()
    assert (tmp_path / "folder").is_dir()


def test_path_exists(env, tmp_path):
    (tmp_path / "file").touch()
    dmp = BaseDumper("file")
    with raises(RuntimeError):
        dmp.commit(tmp_path, env)


@mark.parametrize(
    "dumper, data, res",
    [
        (
            CfgIni,
            {
                "section": {
                    "first": "1",
                    "second": {"one": "1", "two": 2},
                    "third": ["one", "two"],
                }
            },
            (
                "[section]\n"
                "first = 1\n"
                "second = \n\tone = 1\n\ttwo = 2\n"
                "third = \n\tone\n\ttwo\n"
                "\n"
            ),
        ),
        (
            Toml,
            {"section": {"first": "1", "second": 2, "third": ["one", "two"]}},
            ("[section]\n" 'first = "1"\n' "second = 2\n" 'third = [ "one", "two",]\n'),
        ),
        (
            Requirement,
            {None: ("first", "second", "third")},
            "first\nsecond\nthird",
        ),
        (
            Jinja,
            Template("first\nsecond\nthird\n"),
            "first\nsecond\nthird",
        ),
    ],
)
def test_dumpfile(dumper, data, res, env, tmp_path):
    dmp = dumper("file")
    dmp.commit(tmp_path, env)
    dmp.dump_in(data)
    assert (tmp_path / "file").read_text() == res
