from __future__ import print_function
from __future__ import absolute_import
import os
import re
import logging
import platform
import inspect
import json
import datetime
from ..common import *

MODULEFILE = re.sub('\.py', '',
                            os.path.basename(inspect.stack()[0][1]))


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            encoded_object = obj.strftime('%s')
        else:
            encoded_object = json.JSONEncoder.default(self, obj)
        return encoded_object


def fetchprocessor(modules=[]):
    ldict = {"step": MODULEFILE + "/" + inspect.stack()[0][3],
             "hostname": platform.node().split(".")[0]}
    l = logging.LoggerAdapter(fetch_lg(), ldict)
    #
    fetched = {}
    fetchable = {}
    for m in modules:
        try:
            fetchable[m] = __import__("sillyfacter.{}".format(m),
                                      fromlist=[m],
                                      level=0)
        except Exception as _:
            l.exception("Import exception for module '{}'".format(m))
            l.error("Import failure for module '{}'".format(m))
        else:
            l.info("Import success for module '{}'".format(m))
    #
    for modulename, moduleobj in fetchable.iteritems():
        try:
            fetched[modulename] = getattr(moduleobj, "fetch")()
        except Exception as _:
            l.exception("fetch failure for module {}, {}".format(modulename,
                                                                 _))
        else:
            l.info("fetch success for module {}".format(modulename))
    jsonstr = json.dumps(fetch2json(fetched),
                         sort_keys=True,
                         indent=4,
                         cls=DateTimeEncoder,
                         separators=(',', ': '))
    return jsonstr


def lookup(f, t=None):
    if "filesystem" in f:
        fs_list = f["filesystem"]
    else:
        fs_list = {}
    if "nslookup" in f:
        ns_cache = f["nslookup"]
    else:
        ns_cache = {}

    def _fslookup(dev=None, mount=None):
        retval = (None, None)
        if dev is not None:
            key, val, get = "dev", dev, "mount"
        elif mount is not None:
            key, val, get = "mount", mount, "dev"
        else:
            return retval
        for fs in fs_list:
            if fs[key] and fs[key] == val:
                if fs[get]:
                    retval = (fs[get], fs["fstype"])
                    break
        return retval

    def _nslookup(ip=None):
        retval = None
        if ip is not None:
            retval = ip
            if ip not in ns_cache:
                ns_cache[ip] = fetch_dns(ip)
            retval = ns_cache[ip]
        return retval

    if t is None:
        return _fslookup, _nslookup
    elif t == "fslookup":
        return _fslookup
    else:
        return _nslookup


def fetch2json(f):
    myfslookup, mynslookup = lookup(f)
    fetched = {}
    fetched["_scan_id"] = platform.node()
    fetched["_scan_time"] = datetime.datetime.now()
    fetched["has"] = {}
    fetched["had"] = {}

    # host main
    if "os" in f:
        for item, val in f["os"].iteritems():
            fetched[item] = val

    # special
    if "eman" in f:
        for item, val in f["eman"].iteritems():
            if re.match('eman_.*_[0-9]+', item):
                n = re.match('(eman_.*)_[0-9]+', item).group(1)
                try:
                    fetched[n].append(val)
                except:
                    fetched[n] = [val]
            else:
                fetched[item] = val

    # host filesystems
    if "filesystem" in f:
        fetched["has"]["filesystem"] = f["filesystem"]

    # host networks
    if "network" in f:
        fetched["has"]["network"] = []
        for item in f["network"]:
            newitem = {}
            newitem["ifname"] = item["ifname"]
            newitem["ip"] = item["ip"]
            #if newitem["ip"] in f["nslookup"]:
            #    newitem["hostname"] = f["nslookup"][newitem["ip"]]
            fetched["has"]["network"].append(newitem)

    # host procs
    if "process" in f:
        fetched["has"]["process"] = []
        for pid in f["process"]:
            _process_type = set()
            newitem = {}
            newitem["pid"] = pid
            newitem["commandline"] = f["process"][pid]["cmdline"]
            newitem["exe"] = f["process"][pid]["exe"]
            if "exe_fs" in f["process"][pid]:
                newitem["exe_fs"] = f["process"][pid]["exe_fs"]
            newitem["user"] = f["process"][pid]["user"]
            newitem["createtime"] = f["process"][pid]["create_time"]
            if fetched["boottime"] + datetime.timedelta(seconds=600) \
                    > newitem["createtime"]:
                _process_type.add("startup-prog")
            else:
                _process_type.add("user-prog")
            #
            # proc network conn
            if "connections" in f["process"][pid]:
                newitem["connections"] = []
                newconns = f["process"][pid]["connections"]
                for conn in newconns:
                    conn_src = conn[0]
                    conn_src_ip = ":".join(conn_src.split(':')[:-1])
                    conn_src_port = ":".join(conn_src.split(':')[-1:])
                    conn_src_host = conn_src_ip
                    conn_dst = conn[1]
                    if conn_dst is not None:
                        conn_dst_ip = ":".join(conn_dst.split(':')[:-1])
                        conn_dst_port = ":".join(conn_dst.split(':')[-1:])
                        conn_dst_host = conn_dst_ip
                        _process_type_network = "network-client"
                    else:
                        conn_dst_port = "*"
                        conn_dst_ip = "0.0.0.0"
                        conn_dst_host = "*"
                        _process_type_network = "network-daemon"
                    conn_pair = {"source": conn_src_host + ":" + conn_src_port,
                                 "destination": conn_dst_host +
                                 ":" + conn_dst_port}
                    newitem["connections"].append(conn_pair)
                    _process_type.add(_process_type_network)
            #
            # proc open mounts
            if "open" in f["process"][pid]:
                newitem["open"] = {"filesystem": []}
                open_fs = set()
                mountpairs = f["process"][pid]["open"]
                for mountpair in mountpairs:
                    if "fs" in mountpair:
                        fs = mountpair["fs"]
                        open_fs.add(fs)
                        _, fstype = myfslookup(dev=fs)
                        if fstype is not None and len(fstype) > 0:
                            _process_type.add("{}-client".format(fstype))
                newitem["open"]["filesystem"] = list(open_fs)
            newitem["type"] = list(_process_type)
            fetched["has"]["process"].append(newitem)
    if "user" in f:
        users = f["user"]
        if "current" in users:
            fetched["has"]["user"] = users["current"]
        if "last" in users:
            fetched["had"]["user"] = users["last"]
    #
    return fetched
