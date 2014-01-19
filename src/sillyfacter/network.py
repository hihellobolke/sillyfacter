from __future__ import print_function
from __future__ import absolute_import
import psutil
import os
import platform
import re
import netifaces
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
    l.info("Gathering network info...")
    nwio = psutil.net_io_counters(pernic=True)
    nw = []
    for i in netifaces.interfaces():
        try:
            ip = netifaces.ifaddresses(i)[2][0]['addr']
            recv = nwio[i].bytes_recv
            sent = nwio[i].bytes_sent
            nw.append({"ip": ip, "recv": recv, "sent": sent, "ifname": i})
        except:
            ip = None
            recv = nwio[i].bytes_recv
            sent = nwio[i].bytes_sent
            nw.append({"ip": ip, "recv": recv, "sent": sent, "ifname": i})
        l.debug("Adding interface '{}' with ip {}".format(i, str(ip),))
    return nw
