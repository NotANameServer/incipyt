# incipyt

*It begins...*

incipyt \[ˈɪŋkɪpɪt̪\] is a command-line tool that bootstraps a Python project.

	$ pip install incipyt

## Usage

incipyt is *not* opinated, by default it setups the tools recommanded in the
[PyPA/packaging-projects] tutorial: [pyproject.toml] and [setuptools] in
addition to [git] and [sphinx] which are de-facto standard.

	$ python -m incipyt mynewproject
	Project Name [mynewproject]:
	Author [John Doe]:
	Author email [john.doe@users.noreply.github.com]: john.doe@example.com
	License [MIT]:
	$ tree mynewproject
	mynewproject/
	├── docs/
	│   ├── _build
	│   ├── conf.py
	│   ├── index.rst
	│   ├── make.bat
	│   ├── Makefile
	│   ├── _static
	│   └── _templates
	├── .git/
	├── .gitignore
	├── LICENSE
	├── pyproject.toml
	├── README.md
	├── setup.cfg
	├── setup.py
	├── src/
	│   └── mynewproject/
	│       └── __init__.py
	├── tests/
	└── version.txt

incipyt provides a rich command line interface so you can choose various build
systems, version control system, virtual environments, documentation software,
linters, formatters, etc.

	$ python -m incipyt --help

## Contribute

incipyt is released under the MIT license and is open to contributions

    git clone https://github.com/NotANameServer/incipyt
    cd incipyt
    python3 -m venv .env
    .env/bin/pip install flit
    .env/bin/flit install --pth-file --deps develop
    .env/bin/pytest

[PyPA/packaging-projects]: https://packaging.python.org/tutorials/packaging-projects/
[pyproject.toml]: https://www.python.org/dev/peps/pep-0518/
[setuptools]: https://pypi.org/project/setuptools/
[git]: https://git-scm.com/
[sphinx]: https://www.sphinx-doc.org/en/master/
