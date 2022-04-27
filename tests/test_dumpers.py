from pytest import fixture, mark, raises

from incipyt._internal.dumpers import CfgIni, TextFile, Toml
from incipyt import project


@fixture
def reset_environ():
    project.environ.clear()


@mark.parametrize("dumper", (CfgIni, Toml, TextFile))
def test_format_path(dumper, reset_environ, tmp_path):
    dmp = dumper("{first}/{second}.ext")
    project.environ["first"] = project.EnvValue("folder", confirmed=True)
    project.environ["second"] = project.EnvValue("file", confirmed=True)
    dmp.commit(tmp_path)
    assert dmp.format_path() == tmp_path / "folder" / "file.ext"


@mark.parametrize("dumper", (CfgIni, Toml, TextFile))
def test_mkdir(dumper, reset_environ, tmp_path):
    dmp = dumper("folder/file")
    dmp.commit(tmp_path)
    dmp.mkdir()
    assert (tmp_path / "folder").is_dir()


@mark.parametrize("dumper", (CfgIni, Toml, TextFile))
def test_path_exists(dumper, reset_environ, tmp_path):
    (tmp_path / "file").touch()
    dmp = dumper("file")
    with raises(FileExistsError):
        dmp.commit(tmp_path)


@mark.parametrize(
    "dumper, data, res",
    [
        (
            CfgIni,
            {
                "section": {
                    "first": "1",
                    "second": {"one": "1", "two": "2"},
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
            {
                "section": {
                    "first": "1",
                    "second": {"one": "1", "two": "2"},
                    "third": ["one", "two"],
                    "fourth": {"one": {"two": "2"}},
                    "fifth": [
                        {"one": "1.1", "two": "1.2"},
                        {"one": "2.1", "two": "2.2"},
                    ],
                }
            },
            (
                "[section]\n"
                'first = "1"\n'
                'third = [ "one", "two",]\n'
                "[[section.fifth]]\n"
                'one = "1.1"\n'
                'two = "1.2"\n'
                "\n"
                "[[section.fifth]]\n"
                'one = "2.1"\n'
                'two = "2.2"\n'
                "\n"
                "[section.second]\n"
                'one = "1"\n'
                'two = "2"\n'
                "\n"
                "[section.fourth.one]\n"
                'two = "2"\n'
            ),
        ),
        (
            TextFile,
            ["first", "second", "third"],
            "first\nsecond\nthird\n",
        ),
    ],
)
def test_dumpfile(dumper, data, res, reset_environ, tmp_path):
    dmp = dumper("file")
    dmp.commit(tmp_path)
    dmp.dump_in(data)
    assert (tmp_path / "file").read_text() == res
