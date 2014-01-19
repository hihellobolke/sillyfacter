from __future__ import print_function
from __future__ import absolute_import
import os
import platform
import re
import json
import logging
import inspect
from .common import *


MODULEFILE = re.sub('\.py', '',
                    os.path.basename(inspect.stack()[0][1]))


def fetch(host=platform.node()):
    ldict = {"step": MODULEFILE + "/" + inspect.stack()[0][3],
             "hostname": platform.node().split(".")[0]}
    l = logging.LoggerAdapter(fetch_lg(), ldict)
    #
    l.info("Gathering host EMAN info...")

    eman = Command(
        ["/auto/ecs/bin/eman-cli", "host", "show", "--json", "--host=" + host,
         "--flatten"])
    ret = {}
    if eman.run(maxtime=60) is not None:
        output = eman.output
        try:
            e = json.loads(output)
            e = e[list(e.keys())[0]]
            for k in ["eman_department_numner", "eman_city",
                      "eman_hard_serial", "eman_console_url",
                      "eman_smartnet_site_id", "eman_in_data_center",
                      "eman_building_id", "eman_host_id_linux",
                      "eman_support_group", "eman_hostmon",
                      "eman_model_linux", "eman_virtual_machine",
                      "eman_contact_1", "eman_contact_2", "eman_contact_3",
                      "eman_contact_4", "eman_contact_5", "eman_contact_6",
                      "eman_contact_7", "eman_contact_8", "eman_contact_9",
                      "eman_contact_10", "eman_contact_11", "eman_contact_12"]:
                if k[5:] in e:
                    ret[k] = e[k[5:]]
            host_priority = "100"
            for k in e.keys():
                if re.match('hostmon_.*', k, re.IGNORECASE):
                    s = re.search('[1-6]', e[k])
                    if s is not None:
                        if int(s) < int(host_priority):
                            host_priority = s
            if host_priority != "100":
                ret["eman_hostmon"] = host_priority
        except:
            pass
    return ret
