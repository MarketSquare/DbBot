FailBot
=======

FailBot is a Python script used to produce a summary web page about the failing
suites, tests and keywords, using the information stored in a DbBot database.

Please adjust (the barebone) HTML pages inside directory 'templates' to your needs.


Requirements
------------
* Python 2.6 or newer installed
* DbBot
* DbBot produced database, e.g. robot_results.db


Setup
-----

Please make sure you have DbBot installed somewhere and it's root in your PYTHONPATH.

With Bash:

    export PYTHONPATH=$PYTHONPATH:/path/to/DbBot

You may also want to add this line to your .bash_profile to avoid running
the command in every new shell.

On Windows:

    set PYTHONPATH=%PYTHONPATH%;C:\path\to\DbBot


Usage
-----
The executable is 'failbot' in directory 'bin'. Run it from command-line:

    bin/failbot [options]

Required options are:

Short format    | Long format             | Description
--------------- |-------------------------| ------------------------------------------
-o              | --output                 | Output HTML file name

Additional options are:

Short format    | Long format             | Description
--------------- |-------------------------| ------------------------------------------
-v              | --verbose               | Be verbose about the operation
-b DB_FILE_PATH | --database=DB_FILE_PATH | SQLite database of test run results (robot_results.db by default)

On Windows environments, you might need to rename the executable to have the '.py'
file extension ('bin/failbot' -> 'bin/failbot.py').


Usage examples
--------------

The output HTML filename is always required:

    failbot -o index.html

You might want to create the output somewhere under your public_html:

    failbot -o /home/<username>/public_html/index.html

If -b/--database is not specified, a database file 'robot_results.db' is used by default.

With a non-default named database:

    failbot -f atest/testdata/one_suite/output.xml -b my_own_database.db


Directory structure
-------------------

Directory | Description
----------|------------
bin       | Contains the executable. You may want to append this directory to your PATH.
templates | HTML templates used to produced the summary page.
failbot   | Contains the modules used by FailBot.
