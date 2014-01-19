from __future__ import print_function
from __future__ import absolute_import
import psutil
import platform
import time
import logging
import inspect
import os
import re
from .common import *


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
    host_props["release"] = platform.release()
    host_props["system"] = platform.system()
    host_props["hostname"] = platform.node()
    host_props["name"] = host_props["hostname"]
    host_props["memory"] = psutil.virtual_memory().total
    host_props["memory_used"] = psutil.virtual_memory().percent
    host_props["cpu"] = psutil.NUM_CPUS
    host_props["boottime"] = psutil.get_boot_time()
    host_props["cpu_used"] = psutil.cpu_percent(interval=1, percpu=False)
    #host_props = dict(
    #    list(host_props.items()) + list(fetch_host_eman().items()))
    for i in host_props:
        l.debug("{:<15}: {}".format(i, host_props[i]))
    return host_props
