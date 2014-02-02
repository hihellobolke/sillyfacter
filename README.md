# Sillyfacter

Sillyfacter prints JSON facts related to the **state** of the system. The state here mean overview of the process running, their connections and open files. You can also pass mongodb url to store in database.

Current focus on:
  - Portable *.nix 
  - Expandable using custom agents/modules
  - Output to stdout as JSON or write to mongo db

To be done:
  - Output to RabbitMQ

More info: [sillyfacter at github](https://github.com/hihellobolke/sillyfacter)


### Installation


#### Requirements

Desgined in Python 2.7, for *nix systems. Tested on recent Mac OS X, RHEL (v5.5, v6.2), Ubuntu (v13). The Python package dependencies are:
* netaddr
* netifaces
* psutil
* pymongo (for writing to MongoDB)
* pip >= v1.5.1
* pika (for writing to RabbitMQ) 


But these are taken care by **pip** during installation

#### Using pip

###### Upgrade pip to v1.5

```
  # Needs pip v1.5
  # So just upgrade it anyways...
  pip install --upgrade pip
```

###### Pip install
The netifaces module is a bit irritating... so have to use extra options.

```
  pip install --upgrade --allow-all-external --allow-unverified netifaces sillyfacter
  # --upgrade ensures latest versions
  # --allow-all-external and --allow-unverified is needed for netifaces :-(

```

#### From source:
On Debian
  - Ensure following things are installed
    - ```apt-get install python-dev build-essential```
    - ```apt-get install libbz2-dev libssl-dev libsqlite3-dev libreadline6-dev ncurses-dev```
  - Download installer bash script and run it
    - ```wget https://raw.github.com/hihellobolke/sillyfacter/master/installer.bash```
    - ```bash installer.bash```

### Usage

Just execute **sillyfacter** and it should output result back in JSON. If you like to store output directly in a MongoDB, pass mongodb url using ``` --out mongodb://mydb/ ```. Otherwise it just dumps JSON to console.

#### Simple JSON output

```
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
```

#### Storing facts directly in MongoDB

Stores JSON facts directly in to mongodb (uses pymongo). The document *_id* defaults to *hostname* fact, collection defaults to "sillyfacter". Documents are overwritten. Timestamps are converted to Datetime so their types are preserved :-)

```
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

```

#### Help?

And yes there some **--help** too.

```
    $ python sillyfacter --help
    usage: test_sillyfacter.py [-h] [--modules MODULES] [--out OUT] [--log LOG]
                               [--verbose] [--scan {auto,new,last}] [--raw]
                               [--version]

    Sillyfacter fetches facts about the state of the system. Gathers process, open
    file, socket info and then outputs a JSON (currently). Designed for dependency
    mappings.

    optional arguments:
      -h, --help            show this help message and exit
      --modules MODULES     "all" or comma seperated list of modules to be
                            executed. Default is "all" which is expanded to
                            include "process,network,user,os,filesystem".
      --out OUT             Pass URL for the backend mongo database (E.g.
                            mongodb://localhost:27017/). If nothing is supplied it
                            dumps JSON to stdout
      --log LOG             file to write logs to, otherwise logs are written to
                            console
      --verbose, -v         Use multiple "-v" options
      --scan {auto,new,last}
                            [NOT IMPLEMENTED] choose the scan type, usually "auto"
                            is the best. [auto]
      --raw                 [NOT IMPLEMENTED] Use raw output, default is false
      --version             show program's version number and exit

```
### Motivation

Why no facter in pure Python that outputs in JSON?


### Contributors

* More info: https://github.com/hihellobolke/sillyfacter

### License

This is Apache Licenced.
