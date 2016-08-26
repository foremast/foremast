=================
How To Contribute
=================

Contributions to Foremast are welcome.

Getting Started
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

Documentation
^^^^^^^^^^^^^

Use reStructuredText for docstrings and documentation. For docstrings, follow
:ref:`napoleon:example_google`. For documentation pages, follow the strong
guidelines from Python with :ref:`pythondev:documenting`.

.. _Issue: https://github.com/gogoit/foremast/issues
.. _Pull Request: https://github.com/gogoit/foremast/pulls
