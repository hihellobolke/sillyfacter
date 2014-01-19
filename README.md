## Sillyfacter *WORK-IN-PROGRESS*

Sillyfacter prints JSON facts related to the **state** of the system. The state here mean overview of the process running, their connections and open files. Agenda:
  - Portable *.nix
  - Expandable using custom agents/modules
  - Output/filter to file, or database using pymongo or REST based neo4j.

### Requirements

Desgined in Python 2.7, for *nix systems. Tested on Mac, RHEL, Solaris. The Python package dependencies are:
  - netaddr
  - netifaces
  - psutil

But these cab be taken care by using **pip** for installation

## Installation
#### Using pip 
```
  # Needs pip v1.5
  pip install --upgrade --allow-all-external --allow-unverified netifaces sillyfacter
  # --upgrade ensures latest versions
  # --allow-all-external and --allow-unverified is needed for netifaces :-(

  # To upgrade pip
  pip install --ugrade pip
  
```

#### From source:
On Debiam
  - Ensure following things are installed
    - ```apt-get install python-dev build-essential```
    - ```apt-get install libbz2-dev libssl-dev libsqlite3-dev libreadline6-dev ncurses-dev```
  - Download installer bash script and run it
    - ```wget https://raw2.github.com/hihellobolke/sillyfacter/master/installer.bash && bash installer.bash```

### Usage
Just execute **sillyfacter** and it should output result back in JSON

```
$ sillyfacter |head -20
{'boottime': 1389928960.0,
 'cpu': 8,
 'cpu_used': 5.5,
 'had': {'user': ['gautsing', 'wtmp', 'root', 'reboot', 'shutdown']},
 'has': {'filesystem': [{'dev': '/dev/disk0s2',
                         'fstype': 'hfs',
                         'mount': '/'},
                        {'dev': 'map -hosts',
                         'fstype': 'autofs',
                         'mount': '/net'},
                        {'dev': 'map auto_home',
                         'fstype': 'autofs',
                         'mount': '/home'}],
         'network': [{'ifname': 'lo0', 'ip': '127.0.0.1'},
                     {'ifname': 'gif0', 'ip': None},
                     {'ifname': 'stf0', 'ip': None},
                     {'ifname': 'en0', 'ip': '192.168.1.10'},
                     {'ifname': 'p2p0', 'ip': None},
                     {'ifname': 'bbptp0', 'ip': None}],
         'process': [{'commandline': '/System/Library/Frameworks/CoreServices.frame
```

And yes there some **--help** too.

```
$ sillyfacter -h
usage: sillyfacter [-h] [--modules MODULES] [--out OUT] [--log LOG]
                   [--verbose] [--scan {auto,new,last}] [--raw] [--version]

Sillyfacter fetches facts about the state of the system. Gathers process, open
file, socket info and then outputs a JSON (currently). Designed for dependency
mappings.

optional arguments:
  -h, --help            show this help message and exit
  --modules MODULES     comma seperated list of modules to be executed.
                        Default list is "process,network,user,os,filesystem".
  --out OUT             [NOT IMPLEMENTED] URL for the backend database
                        (neo4j/mongo) or a file to write json output to. If
                        nothing is supplied it dumps JSON to stdout
  --log LOG             file to write logs to, otherwise logs are written to
                        console
  --verbose, -v         For higher verbosity use multiple "-v" options
  --scan {auto,new,last}
                        [NOT IMPLEMENTED] choose the scan type, usually "auto"
                        is the best. [auto]
  --raw                 [NOT IMPLEMENTED] Use raw output, default is false
  --version             show program's version number and exit
```
## Motivation

Why no facter for pure Python that outputs in JSON?


## Contributors

Email g@ut.am

## License

This is Apache Licenced.
