===========
sillyfacter
===========

Sillyfacter prints JSON facts related to the **state** of the system.
The state here mean overview of the process running, their connections
and open files. You can also pass mongodb url to store in database.

Current focus on:

 - Portable \*.nix
 - Expandable using custom agents/modules
 - Output/filter to stdout or mongo db using pymongo or (Celery?)

**For more info:** `sillyfacter at github`_

Installation
~~~~~~~~~~~~

Requirements
^^^^^^^^^^^^^

Desgined in Python 2.7, for \*nix systems. Tested on Mac, RHEL, Solaris.
The Python package dependencies are:

- netaddr
- netifaces
- psutil
- pymongo
- pip >= v1.5.1

But these are taken care by **pip** during installation

Using pip
^^^^^^^^^

::

      # Needs pip v1.5
      # So just upgrade it anyways...
      pip install --ugrade pip


      pip install --upgrade --allow-all-external --allow-unverified netifaces sillyfacter
      # --upgrade ensures latest versions
      # --allow-all-external and --allow-unverified is needed for netifaces :-(

From source:
^^^^^^^^^^^^

On Debian:
Ensure following things are installed:

- ``apt-get install python-dev build-essential``
- ``apt-get install libbz2-dev libssl-dev libsqlite3-dev libreadline6-dev ncurses-dev``

Download installer bash script and run it

- ``wget https://raw.github.com/hihellobolke/sillyfacter/master/installer.bash``
- ``bash installer.bash``

Usage
~~~~~

Just execute **sillyfacter** and it should output result back in JSON.
If you like to store output directly in a MongoDB, pass mongodb url
using ``--out mongodb://mydb/``. Otherwise it just dumps JSON to
console.

Simple JSON output
^^^^^^^^^^^^^^^^^^

::

    $ sillyfacter
    {
        "_scan_id": "gautsing-mac",
        "_scan_time": "1390293214",
        "arch": "x86_64",
        "boottime": "1390206976",
        "cpu": 8,
        "cpu_used": 10.2,
        "domainname": "",
        "fqdn": "gautsing-mac",
        "hardwareisa": "i386",
        "hardwaremodel": "i386",
        "has": {
            "filesystem": [
                {
                    "dev": "/dev/disk0s2",

Storing facts directly in MongoDB
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Stores JSON facts directly in to mongodb (uses pymongo). The document
\*\_id\* defaults to *hostname* fact, collection defaults to
"sillyfacter". Documents are overwritten. Timestamps are converted to
Datetime so their types are preserved :-)

::

    $ sillyfacter --out mongodb://localhost/factdb
    {
        "_info": {
            "_id": "gautsing-mac",
            "collection": "sillyfacter",
            "db": "factdb",
            "host": "localhost",
            "port": 27017
        },
        "status": "Save success",
        "url": "mongodb://localhost/factdb"
    }

Help?
^^^^^

And yes there some **--help** too.

::

    $ python sillyfacter --help
    usage: sillyfacter [-h] [--modules MODULES] [--out OUT] [--log LOG]
                            [--verbose] [--strict] [--debug]
                            [--scan {auto,new,last}] [--raw] [--version]

    Sillyfacter fetches facts about the state of the system. Gathers process, open
    file, socket info and then outputs a JSON (currently). Designed for dependency
    mappings.

    optional arguments:
      -h, --help            show this help message and exit
      --modules MODULES     comma seperated list of modules to be executed.
                            Default list is "all" which is expanded to include
                            "process,network,user,os,filesystem"
      --out OUT             URL for the backend Mongo database (E.g.
                            mongodb://localhost:27017/). If nothing is supplied it
                            dumps JSON to stdout
      --log LOG             file to write logs to, otherwise logs are written to
                            console
      --verbose, -v         Use multiple "-v" options
      --strict              If selected will error out on every exeption Note:
                            Useful when debugging only [False]
      --debug               If selected will emit very debugging logs if exception
                            are encountered. Note: Useful when debugging only
                            [False]
      --scan {auto,new,last}
                            [NOT IMPLEMENTED] choose the scan type, usually "auto"
                            is the best. [auto]
      --raw                 [NOT IMPLEMENTED] Use raw output, default is false
      --version             show program's version number and exit

Motivation
~~~~~~~~~~

Why no facter in pure Python that outputs in JSON?

Contributors
~~~~~~~~~~~~

- Email: g@ut.am
- More info: https://github.com/hihellobolke/sillyfacter

License
~~~~~~~

This is Apache Licenced.

.. _sillyfacter at github: https://github.com/hihellobolke/sillyfacter
