How to do releases
------------------

Setup
=====

Add the following to `~/.pypirc` file
```
[distutils]
index-servers =
    gogo

[gogo]
repository = https://pypi.example.com
username = username
password = xxxyyyzzz
```

Upload Release
==============

When releasing a new version, the following needs to occur
* Update version in `setup.py`
* Ensure all test via `tox` pass

Once that is taken care of, execute the following:
```
$ python setup.py sdist upload -r gogo
```
