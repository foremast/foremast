=================
How To Contribute
=================

.. contents::
   :local:

Contributions to Foremast are welcome.

Getting Started
---------------

.. _commits:

Commits
^^^^^^^

Follow `semantic commits`_ to make :command:`git log` a little easier to follow.

chore
   something just needs to happen, e.g. versioning
docs
   documentation pages in :file:`_docs/` or docstrings
feat
   new code in :file:`src/`
fix
   code improvement in :file:`src/`
refactor
   code movement in :file:`src/`
style
   aesthetic changes
test
   test case modifications in :file:`test/`

Examples commit messages:

* chore: v10.0
* docs: Add configuration setting
* feat: Create Lambda function
* fix: Retry upload on failure
* refactor: Extract duplicate code
* style: isort, YAPF
* test: Coverage around add permissions

.. _semantic commits: https://seesparkbox.com/foundry/semantic_commit_messages

Branches
^^^^^^^^

Use `slash convention`_ with the same leaders as :ref:`commits`, e.g.:

* chore/v10.0
* docs/configs
* feat/lambda
* fix/deadlock
* refactor/debug_util
* style/lambda_whitespace
* test/lambda_permission

.. _slash convention: http://www.guyroutledge.co.uk/blog/git-branch-naming-conventions/

Documentation
^^^^^^^^^^^^^

* Use reStructuredText for docstrings and documentation
* For docstrings, follow :ref:`napoleon:example_google`
* For documentation pages, follow the strong guidelines from Python with
  :ref:`pythondev:documenting`

.. note::

   * Use :file:`.rst` for regular pages
   * Use :file:`.rest` for pages included using ``.. include:: file.rest``
     (fixes a Sphinx issue that thinks references are duplicated)

Testing
^^^^^^^

Run any unit tests available in ``./tests/``.

.. code-block:: bash

    virtualenv venv
    source ./venv/bin/activate
    pip install -U -r requirements-dev.txt

    tox

Code Submission
---------------

Code Improvement
^^^^^^^^^^^^^^^^

#. See if an `Issue`_ exists

   * Comment with any added information to help the discussion

#. Create an `Issue`_ if needed

Code Submission
^^^^^^^^^^^^^^^

#. See if a `Pull Request`_ exists

   * Add some comments or review the code to help it along
   * Don't be afraid to comment when logic needs clarification

#. Create a Fork and open a `Pull Request`_ if needed

Code Review
^^^^^^^^^^^

* Anyone can review code
* Any `Pull Request`_ should be closed or merged within a week

Code Acceptance
^^^^^^^^^^^^^^^

Try to keep history as linear as possible using a `rebase` merge strategy.

#. One thumb up at minimum, two preferred
#. Request submitter to `rebase` and resolve all conflicts

   .. code:: bash

      # Update `master`
      git checkout master
      git pull

      # Update `feat/new` Branch
      git checkout feat/new
      git rebase master

      # Update remote Branch and Pull Request
      git push -f

#. Merge the new feature

   .. code:: bash

      # Merge `feat/new` into `master`
      git checkout master
      git merge --ff-only feat/new
      git push

#. Delete merged Branch

.. _Issue: https://github.com/gogoit/foremast/issues
.. _Pull Request: https://github.com/gogoit/foremast/pulls
