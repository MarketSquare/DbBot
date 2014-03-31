DbBot
=====

DbBot is a Python script to serialize `Robot Framework`_  output files into
a SQLite database. This way the future `Robot Framework`_ related tools and
plugins will have a unified storage for the test run results.

Requirements
------------

-  `Python`__ 2.6 or newer installed
-  `Robot Framework`_ 2.7 or newer installed

`Robot Framework`_ version 2.7.4 or later is recommended as versions prior to
2.7.4 do not support storing total elapsed time for test runs or tags.

How it works
------------

The script takes one or more `output.xml` files as input, initializes the
database schema, and stores the respective results into a database
(`robot\_results.db` by default, can be changed with options `-b` or
`--database`). If database file is already existing, it will insert the new 
results into that database.

Installation
------------

This tool is installed with pip with command:

::

    $ pip install dbbot

Alternatively you can download the source distribution, extract it and
install using:

::

    $ python setup.py install

What is stored
--------------

Both the test data (names, content) and test statistics (how many did pass or
fail, possible errors occurred, how long it took to run, etc.) related to
suites and test cases are stored by default. However, keywords and related
data are not stored as it might take order of magnitude longer for massive
test runs. You can choose to store keywords and related data by using `-k` or
`--also-keywords` flag.

Usage examples
--------------

Typical usage with a single output.xml file:

::

    python -m dbbot.run atest/testdata/one_suite/output.xml

If the database does not already exist, it's created. Otherwise the test
results are just inserted into the existing database. Only new results are
inserted.

The default database is a file named `robot_results.db`.

Additional options are:

+-------------------+---------------------------+--------------------------+
| Short format      | Long format               | Description              |
+===================+===========================+==========================+
| `-k`              | `--also-keywords`         | Parse also suites' and   |
|                   |                           | tests' keywords          |
+-------------------+---------------------------+--------------------------+
| `-v`              | `--verbose`               | Print output to the      |
|                   |                           | console.                 |
+-------------------+---------------------------+--------------------------+
| `-b DB_FILE_PATH` | `--database=DB_FILE_PATH` | SQLite database for test |
|                   |                           | run results              |
+-------------------+---------------------------+--------------------------+
| `-d`              | `--dry-run`               | Do everything except     |
|                   |                           | store the results.       |
+-------------------+---------------------------+--------------------------+


Specifying custom database name:

::

    $ python -m dbbot.run  -b my_own_database.db atest/testdata/one_suite/output.xml

Parsing test run results with keywords and related data included:

::

    python -m dbbot.run -k atest/testdata/one_suite/output.xml

Giving multiple test run result files at the same time:

::

    python -m dbbot.run atest/testdata/one_suite/output.xml atest/testdata/one_suite/output_latter.xml

Database
--------

You can inspect the created database using the `sqlite3`_ command-line tool:

.. code:: sqlite3

    $ sqlite3 robot_results.db

    sqlite> .tables
    arguments        suite_status     test_run_errors  tests
    keyword_status   suites           test_run_status
    keywords         tag_status       test_runs
    messages         tags             test_status

    sqlite> SELECT count(), tests.id, tests.name
            FROM tests, test_status
            WHERE tests.id == test_status.test_id AND
            test_status.status == "FAIL"
            GROUP BY tests.name;

Please note that when database is initialized, no indices are created by
DbBot. This is to avoid slowing down the inserts. You might want to add
indices to the database by hand to speed up certain queries in your own
scripts.

For information about the database schema, see `doc/robot_database.md`__.

Migrating from Robot Framework 2.7 to 2.8
-----------------------------------------

In Robot Framework 2.8, output.xml has changed slightly. Due this, the
databases created with 2.7 need to migrated to be 2.8 compatible.

To migrate the existing database, issue the following script:

::

    python tools/migrate27to28 -b <path_to_robot_results_db>

Use case example: Most failing tests
------------------------------------

One of the common use cases for DbBot is to get a report of the most commonly
failing suites, tests and keywords. There's an example for this purpose in
`examples/FailBot/bin/failbot`.

Failbot is a Python script used to produce a summary web page of the failing
suites, tests and keywords, using the information stored in the DbBot
database. Please adjust (the barebone) HTML templates in
`examples/FailBot/templates` to your needs.

Writing your own scripts
------------------------

Please take a look at the modules in `examples/FailBot/failbot` as an example
on how to build on top of the classes provided by DbBot to satisfy your own
scripting needs.

License
-------

DbBot is released under the `Apache License, Version 2.0`__.

See LICENSE.TXT for details.

__ https://www.python.org/
__ https://github.com/robotframework/DbBot/blob/master/doc/robot_database.md
__ http://www.tldrlegal.com/license/apache-license-2.0
.. _`Robot Framework`: http://www.robotframework.org
.. _`pip`: http://www.pip-installer.org
.. _`sqlite3`: https://www.sqlite.org/sqlite.html
