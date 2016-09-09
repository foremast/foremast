How To Create Releases
----------------------

Setup
=====

Add the following to ``~/.pypirc`` file

.. code-block:: ini

    [distutils]
    index-servers =
        gogo

    [gogo]
    repository = https://pypi.example.com
    username = username
    password = xxxyyyzzz

Upload Release
==============

When releasing a new version, the following needs to occur:

#. Add version Tag

   .. code:: bash

      git tag -a #.#.#
      git push --tags

#. Ensure all test via ``tox`` pass
#. Generate and upload the package

   .. code:: bash

      python setup.py bdist_wheel upload -r gogo
