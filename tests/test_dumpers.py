from pytest import fixture, mark, raises

from incipyt._internal.dumpers import BaseDumper, CfgIni, Requirement, Toml
from incipyt import project


@fixture
def reset_environ():
    project.environ.clear()


def test_format_path(reset_environ, tmp_path):
    dmp = BaseDumper("{first}/{second}.ext")
    project.environ["first"] = project.EnvValue("folder", confirmed=True)
    project.environ["second"] = project.EnvValue("file", confirmed=True)
    dmp.commit(tmp_path)
    assert dmp.substitute_path() == tmp_path / "folder" / "file.ext"


def test_mkdir(reset_environ, tmp_path):
    dmp = BaseDumper("folder/file")
    dmp.commit(tmp_path)
    dmp.mkdir_in()
    assert (tmp_path / "folder").is_dir()


def test_path_exists(reset_environ, tmp_path):
    (tmp_path / "file").touch()
    dmp = BaseDumper("file")
    with raises(RuntimeError):
        dmp.commit(tmp_path)


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
    ],
)
def test_dumpfile(dumper, data, res, reset_environ, tmp_path):
    dmp = dumper("file")
    dmp.commit(tmp_path)
    dmp.dump_in(data)
    assert (tmp_path / "file").read_text() == res
