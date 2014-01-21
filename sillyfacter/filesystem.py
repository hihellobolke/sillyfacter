from __future__ import print_function
from __future__ import absolute_import
import psutil
import os
import platform
import re
import logging
import inspect
from .common import *


MODULEFILE = re.sub('\.py', '',
                            os.path.basename(inspect.stack()[0][1]))


def fetch():
    ldict = {"step": MODULEFILE + "/" + inspect.stack()[0][3],
             "hostname": platform.node().split(".")[0]}
    l = logging.LoggerAdapter(fetch_lg(), ldict)
    #
    l.info("Gathering filesystem info...")
    fs = []
    for p in psutil.disk_partitions(all=False):
        l.info("Found {} mounted as {}".format(p.device, p.mountpoint))
        partition = {}
        partition = {'dev': p.device,
                     "mount": p.mountpoint,
                     "fstype": p.fstype}
        if (re.match('ext[0-9]|xfs|ufs|btrfs', p.fstype, re.IGNORECASE)):
            try:
                disk_usage = psutil.disk_usage(p.mountpoint)
            except:
                pass
            else:
                partition["total"] = disk_usage.total
                partition["used"] = disk_usage.used
                partition["free"] = disk_usage.free
                partition["percent"] = disk_usage.percent
        fs.append(partition)
    for p in psutil.disk_partitions(all=True):
        if (re.match('nfs|autofs', p.fstype, re.IGNORECASE)):
            l.info("Found '{}' mounted as '{}'".format(p.device, p.mountpoint))
            fs.append(
                {'dev': p.device, "mount": p.mountpoint, "fstype": p.fstype})
    return fs
