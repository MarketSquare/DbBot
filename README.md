DbBot
=====

DbBot is a Python script used to serialize Robot Framework produced test run results,
i.e. output.xml files, into a SQLite database. That way the future Robot Framework
related tools and plugins will have a common storage for the test result data.

The script takes one or more output.xml files as input, initializes the
database schema, produces the respective insert statements and finally commits the results
into the database (robot_results.db by default, can be changed by -b or --database).

Both the test data (names and paths) and test statistics (how many did pass or fail,
possible errors occurred, how long it took to run, etc.) related to suites and test cases
are stored by default. Optionally, keywords can be stored by -k or --also-keywords flag, but
this is not the default behavior as it might take tens of seconds for massive test runs.


Use cases
---------
One of the common use cases is to get a report of the most commonly failing suites,
tests and keywords. DbBot comes with an executable example for this, named 'topfail',
bundled in 'examples/topfail/bin/topfail'.

Topfail is used to produce an html summary based on the test data serialized
into the dbbot database. Feel free to adjust (the very barebone) html templates
in 'topfail/templates' to your needs.

Another possible use case is to build a script that produces an html
summary of the most time-consuming tests, keywords etc.

Take a look at the modules under 'examples/topfail/topfail' on how to extend the
DbBot provided classes to your own scripting needs. You may also want to append
'dbbot/dbbot' directory to your PYTHONPATH if you are building something with
Python that uses the classes.


Requirements
------------

* Python 2.6 or newer installed
* Robot Framework 2.7 or newer installed

Tested and verified on Python 2.7.4 and Robot Framework 2.7.7


Usage
-----
The executable is 'dbbot' under directory 'bin'.

Use the script from command-line: dbbot [options]

Valid command-line options are:

Short format    | Long format             | Description
--------------- |-------------------------| ------------------------------------------
-v              | --verbose               | be verbose about the operation
-b DB_FILE_PATH | --database=DB_FILE_PATH | path to the sqlite3 database for test run results
-d              | --dry-run               | do everything except store results into disk
-k              | --also-keywords         | parse also suites' and tests' keywords
-f              | --files                 | one or more Robot output.xml files

On Windows environments you might need to rename the executable to have the '.py' file extension.


Usage examples
--------------
TODO


Directory structure
-------------------

Directory | Description
----------|------------
atests    | Robot Framework powered acceptance tests for DbBot. Also has some test data.
bin       | Contains the executables, mainly 'dbbot'. You may want to append this directory to your PATH.
dbbot     | Contains the packages used by dbbot. You may want to append this directory to your PYTHONPATH if your scripts are inheriting from the abstract classes in the package 'dbbot'
doc       | Mainly technical documentation about the DbBot database schema.
examples  | Examples that are using the DbBot created database and extending the 'dbbot' modules.
