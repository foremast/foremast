How To Create Releases
----------------------

Creating a New Release
======================

When releasing a new version, the following needs to occur:

#. Pull the latest main branch

   .. code:: bash

      git pull origin main

#. Ensure all test via ``tox`` pass
#. Add version Tag

   .. code:: bash

      git tag -a v#.#.#
      git push --tags

#. Github Actions won `tag` creation will build/publish to PyPI
#. Ensure proper build on: https://test.pypi.org/project/foremast/#history