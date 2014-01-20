from __future__ import print_function
from __future__ import absolute_import
import psutil
import platform
import logging
import inspect
import os
import re
import datetime
from .common import *
##

MODULEFILE = re.sub('\.py', '',
                            os.path.basename(inspect.stack()[0][1]))


def fetch():
    #
    ldict = {"step": MODULEFILE + "/" + inspect.stack()[0][3],
             "hostname": platform.node().split(".")[0]}
    l = logging.LoggerAdapter(fetch_lg(), ldict)
    #
    l.info("Gathering host info...")
    host_props = {}
    host_props["machine"] = platform.machine()
    host_props["arch"] = platform.machine()
    host_props["release"] = platform.release()
    host_props["system"] = platform.system()
    host_props["hostname"] = platform.node()
    host_props["name"] = host_props["hostname"]
    host_props["domainname"] = ".".join(socket.gethostname().split('.')[1:])
    host_props["fqdn"] = socket.gethostname()
    host_props["memory"] = psutil.virtual_memory().total
    host_props["memory_used"] = psutil.virtual_memory().percent
    host_props["cpu"] = psutil.NUM_CPUS
    dt = datetime.datetime.fromtimestamp
    host_props["boottime"] = dt(psutil.get_boot_time())
    host_props["cpu_used"] = psutil.cpu_percent(interval=1, percpu=False)
    host_props["hardwareisa"] = platform.processor()
    host_props["hardwaremodel"] = platform.processor()
    host_props["user"] = os.environ['USER']
    ostype = os.uname()[0]
    if ostype == "Linux":
        host_props["kernel_release"] = platform.uname()[2]
        host_props["kernel_version"] = platform.uname()[2].split('-')[0]
        try:
            host_props_extra = fetch_linux()
        except Exception as _:
            l.exception("unable to fetch linux specific info '{}'".format(_))
            host_props_extra = {}
        host_props = dict(host_props.items() + host_props_extra.items())
    for i in host_props:
        l.debug("{:<15}: {}".format(i, host_props[i]))
    return host_props


def _run_this(c):
    cmd = Command(c)
    retval = None
    if cmd.run() == 0:
        return cmd.output
    else:
        return retval


def _open_read_this(filepath):
    retval = ""
    with open(filepath, 'r') as f:
        retval = f.read()
        retval.strip()
    return retval


def run_parse_lsb():
    lsb_finder = _run_this(["/usr/bin/which", "lsb_release"])
    retval = {}
    if lsb_finder is not None:
        lsbcmd = _run_this([lsb_finder[0].strip(), "-a"])
        if lsbcmd is not None:
            lsb_parsed = {}
            for line in lsbcmd:
                line = line.strip()
                key = line.split(':')[0]
                val = ":".join(line.split(':')[1:]).strip()
                key = key.lower().replace('lsb', '')
                key = key.strip().replace(' ', '_')
                lsb_parsed["lsb_{}".format(key)] = val
            retval = lsb_parsed
    return retval


## Similar to Phacter :-)
def fetch_linux():
    fetch = run_parse_lsb()
    if fetch["lsb_distributor_id"] == 'Ubuntu':
        operatingsystem = "Ubuntu"
        operatingsystemrelease = fetch["lsb_release"]
    elif os.path.isfile('/etc/debian_version'):
        operatingsystem = 'Debian'
        operatingsystemrelease = _open_read_this('/etc/debian_version')
    elif os.path.isfile('/etc/gentoo-release'):
        operatingsystem = 'Gentoo'
        operatingsystemrelease = _open_read_this('/etc/gentoo-release')
    elif os.path.isfile('/etc/fedora-release'):
        operatingsystem = 'Fedora'
        operatingsystemrelease = _open_read_this('/etc/fedora-release')
    elif os.path.isfile('/etc/mandriva-release'):
        operatingsystem = 'Mandriva'
        operatingsystemrelease = _open_read_this('/etc/mandriva-release')
    elif os.path.isfile('/etc/mandrake-release'):
        operatingsystem = 'Mandrake'
        operatingsystemrelease = _open_read_this('/etc/mandrake-release')
    elif os.path.isfile('/etc/redhat-release'):
        operatingsystemrelease = _open_read_this('/etc/redhat-release')
        if re.compile('centos', re.IGNORECASE).search(operatingsystemrelease):
            operatingsystem = 'CentOS'
        else:
            operatingsystem = 'RedHat'
    elif os.path.isfile('/etc/SuSE-release'):
        operatingsystemrelease = _open_read_this('/etc/SuSE-release')
        if re.compile('SUSE LINUX Enterprise Server',
                      re.I).search(operatingsystemrelease):
            operatingsystem = 'SLES'
        else:
            operatingsystem = 'SuSE'
    else:
        operatingsystem = "Unknown"
        operatingsystemrelease = "Unknown"
    fetch["operatingsystem"] = operatingsystem.strip()
    fetch["operatingsystemreleasestring"] = operatingsystemrelease.strip()
    return fetch
