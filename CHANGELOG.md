# Changelog

## [0.4.0](https://github.com/NotANameServer/incipyt/compare/v0.3.0...v0.4.0) (2023-06-10)


### ⚠ BREAKING CHANGES

* bump python to 3.8

### Features

* config file ([83b36a2](https://github.com/NotANameServer/incipyt/commit/83b36a2416c2786d5734e2c1fa306e6c97265559))
* metadata system ([14e761f](https://github.com/NotANameServer/incipyt/commit/14e761f6a5de8dc2710daf0947abec8dcedaee14))
* **metadata:** implement a declarative metadata system for environment variables ([868e85a](https://github.com/NotANameServer/incipyt/commit/868e85af19ce6136a14f57b13894e7f2002e851f))
* **metadata:** metadata field do_not_prompt to bypass prompting ([619c9b7](https://github.com/NotANameServer/incipyt/commit/619c9b776977471f24f9c52b247bf931bc679dea))
* **metadata:** metadata field required and purging mechanism for template ([f7261ca](https://github.com/NotANameServer/incipyt/commit/f7261ca7a1b37dc1830870ffb3acd32fd7497d57))
* **metadata:** stage control on metadata setter ([9b9b097](https://github.com/NotANameServer/incipyt/commit/9b9b097bfd18d099292caeff2db3364da0e900d7))
* split project.py in multiple files ([03cf0e2](https://github.com/NotANameServer/incipyt/commit/03cf0e2d09997659ca9be28ccc34d6656260b577))
* use project.environ to store additional options ([f8e8a6a](https://github.com/NotANameServer/incipyt/commit/f8e8a6a7e68f7a356a55b04b0202b3a3a91e6587))


### Bug Fixes

* **build:** add min_version for dependency slots ([e972377](https://github.com/NotANameServer/incipyt/commit/e972377aebcd661e9ac2f7dab6bcda92cd54e2ce))
* **build:** add required metadata for mandatory fields for poetry builder ([b34cce2](https://github.com/NotANameServer/incipyt/commit/b34cce20a1c289440d061873b42960d2bbde6aa5))
* **build:** remove unused **kwargs in __init__ and explicit check_build parameter ([1b91c65](https://github.com/NotANameServer/incipyt/commit/1b91c659e1470d83e0e9d46c3622447c6b3a3256))
* bumps toml to tomli_w for dumpers.Toml ([9fe71ce](https://github.com/NotANameServer/incipyt/commit/9fe71cebf310703f92520f5ed619e232aa735fc2))
* **main:** don't drop args[0] when importing ([665b5a4](https://github.com/NotANameServer/incipyt/commit/665b5a463ebeebd27d97e82cf7ca27cf568d6209))
* **README:** mix tabs and spaces ([9c153c9](https://github.com/NotANameServer/incipyt/commit/9c153c987c885e6c4c4386e6f64f3c9166fbcb79))
* replace |= operator by update function for UserDict based class ([7aa6ab7](https://github.com/NotANameServer/incipyt/commit/7aa6ab70fedee3e5120d2aefd95bf36d2f5cd0da))
* use a list instead of a set when parsing string patterns ([e688458](https://github.com/NotANameServer/incipyt/commit/e68845872b21afc69485054372abd5adeb3921ec))
* **venv:** use an hidden option as virtual env folder name ([5cbfd3f](https://github.com/NotANameServer/incipyt/commit/5cbfd3f00084b73d8e36b34b48e53aa31e33e3c2))


### Miscellaneous Chores

* bump python to 3.8 ([2120661](https://github.com/NotANameServer/incipyt/commit/21206618a1c319e3a08706c52c7c60e0134946a8))

## [0.3.0](https://github.com/NotANameServer/incipyt/compare/v0.2.0...v0.3.0) (2023-04-09)


### Features

* **build:** flit supports ([3eccc8d](https://github.com/NotANameServer/incipyt/commit/3eccc8d976af066285a6892ed2abb384544e8988))
* **build:** hatch support ([c44647f](https://github.com/NotANameServer/incipyt/commit/c44647f5727cbdadba667563fd86f97f7c6537e9))
* **build:** new generic abstract class for PEP 517 builder ([93a01f5](https://github.com/NotANameServer/incipyt/commit/93a01f5131afc2e600a5a04d8ebf34a4f9f1d671))
* **build:** pdm supports ([a6c0d7b](https://github.com/NotANameServer/incipyt/commit/a6c0d7b21b6c3c2a782f3719828b000c9181cb59))
* **build:** poetry supports ([3292381](https://github.com/NotANameServer/incipyt/commit/3292381ca3ef7a0c67f9859f5ea5b9811433eed2))
* command line options to select tools ([932e250](https://github.com/NotANameServer/incipyt/commit/932e250cc8608d2e8b22f5a6b82465cafc519e84))
* copy template files to project ([7aa68e6](https://github.com/NotANameServer/incipyt/commit/7aa68e6f6df4d986c849501cf95b74132a405aaf))
* **git:** include a generic gitignore ([ec80c7d](https://github.com/NotANameServer/incipyt/commit/ec80c7d6eb2fe95a0ae9e86269d13852ed6d0a63))
* **git:** prompt user to set git config user.name ([975eb17](https://github.com/NotANameServer/incipyt/commit/975eb1761ab907db8ff4de5dcbae94d1aa3f918a))
* **license:** choose a license from the CLI ([df1a0fd](https://github.com/NotANameServer/incipyt/commit/df1a0fd23d93cae3ebcb94705bc8e801e89b2511))
* **setuptools:** keep classifiers and deps sorted ([d6b99e6](https://github.com/NotANameServer/incipyt/commit/d6b99e6e35cfd540f5c42a4bbdee5deacc7dc244))


### Bug Fixes

* **build:** make legacy Setuptools tool compliant with PEPs specification ([6a816e7](https://github.com/NotANameServer/incipyt/commit/6a816e7fccbe8ace7998186d722ec7cec5321518))
* **git:** use empty author when git config fail ([c32ebf3](https://github.com/NotANameServer/incipyt/commit/c32ebf3c7b0814f1ecb2b084bdbcfa5d1df54e7e))
* **venv:** upgrade pip to last version after venv creation ([537622b](https://github.com/NotANameServer/incipyt/commit/537622b11c9ea52fda9d52ede1138a54e147b877))

## [0.2.0](https://www.github.com/NotANameServer/incipyt/compare/v0.1.0...v0.2.0) (2022-05-28)


### Features

* advanced logging configuration ([3f5e470](https://www.github.com/NotANameServer/incipyt/commit/3f5e470fd1336cbb5ccc65f2a50d054d344b8af1)), closes [#22](https://www.github.com/NotANameServer/incipyt/issues/22)
* crash when git is missing ([151f8a8](https://www.github.com/NotANameServer/incipyt/commit/151f8a8adca513556a4e21494e50379f561cef13))
* **setuptools:** specific var for python_requires ([42ce7be](https://www.github.com/NotANameServer/incipyt/commit/42ce7be70d55c6a0f321c26acc1477f0c18639ce)), closes [#31](https://www.github.com/NotANameServer/incipyt/issues/31)


### Bug Fixes

* **venv:** --upgrade-deps option missing on mint ([80b0bcf](https://www.github.com/NotANameServer/incipyt/commit/80b0bcfbee653b0530ede035daad15ebb12b099e)), closes [#27](https://www.github.com/NotANameServer/incipyt/issues/27)

## 0.1.0 (2022-04-27)


### Features

* Central Hierarchy + Environment design populated by Actions ([c6ba581](https://www.github.com/NotANameServer/incipyt/commit/c6ba5811dc4ac921d208e19ba5141c03fe227130))
* first proposal for TemplateDict internal ([682e437](https://www.github.com/NotANameServer/incipyt/commit/682e437171790389ee1acab345977154e55f8c07))
* improve TemplateDict use cases ([f120870](https://www.github.com/NotANameServer/incipyt/commit/f12087096c5a3d6daf6c1b00b546d6d1b87f9c9e))
* project initialization ([de1b463](https://www.github.com/NotANameServer/incipyt/commit/de1b4631d5cd0430c11ee558daf354343cb05e2d)), closes [#3](https://www.github.com/NotANameServer/incipyt/issues/3)
* system.Environement specifications as dict-like class ([e47029c](https://www.github.com/NotANameServer/incipyt/commit/e47029c5eb2e4e6a450329540401cde1fbdd4f96))
* TemplateList proxy for configuration ([48c25c9](https://www.github.com/NotANameServer/incipyt/commit/48c25c924f6cb0882a871c3a6b4d0939088808d5))
* Using click for interactive cli ([22188e7](https://www.github.com/NotANameServer/incipyt/commit/22188e7bbcb0011252fcd7bc80ae5515d6dce93a))


### Bug Fixes

* Cfg and TOML dumpers behaviors ([928d999](https://www.github.com/NotANameServer/incipyt/commit/928d999f82f95930c8479a874b534468ebd4eb38))
* miscellaneous text files for SetupTools ([9dbdac3](https://www.github.com/NotANameServer/incipyt/commit/9dbdac3b6f77dac337dfe750c9422c813947af13))
* remove dumpers instanciation classmethod ([9a8994a](https://www.github.com/NotANameServer/incipyt/commit/9a8994abae5b883469d7c5d281d2f99f30159608))
* remove unnecessary else branch ([9f850d9](https://www.github.com/NotANameServer/incipyt/commit/9f850d9c5f78226b26a230b49ada9c06f954de8e))
* solve click.argument issue with Path object for type arg ([68bc301](https://www.github.com/NotANameServer/incipyt/commit/68bc301137830f24943193ff1aabe2301c3d8fac))
* use proper syntax for named tuple ([4ff7193](https://www.github.com/NotANameServer/incipyt/commit/4ff71938eb3c220dfaad5e962e903ef182f7b112))
* various fixes ([f1334af](https://www.github.com/NotANameServer/incipyt/commit/f1334afa0838f3ffcccfd570ada315874c69eec0))
* windows compatibility ([686f8fb](https://www.github.com/NotANameServer/incipyt/commit/686f8fb0085474f3b23a159fd169788f37a577d6))


### Documentation

* improve utils docs ([aafff78](https://www.github.com/NotANameServer/incipyt/commit/aafff78356cca0976614384832b3f596bcd1c1c1))
* incipyt help message ([3ab6d16](https://www.github.com/NotANameServer/incipyt/commit/3ab6d16c0c6a2ae30ea0bcd10d91ea6d70ab80cd))
