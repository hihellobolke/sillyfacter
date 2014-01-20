from __future__ import print_function
from __future__ import absolute_import
import psutil
import os
import platform
import re
import netaddr
import logging
import inspect
import datetime
from collections import deque
from .common import *


MODULEFILE = re.sub('\.py', '',
                            os.path.basename(inspect.stack()[0][1]))


def fetch():
    ldict = {"step": MODULEFILE + "/" + inspect.stack()[0][3],
             "hostname": platform.node().split(".")[0]}
    l = logging.LoggerAdapter(fetch_lg(), ldict)
    #
    l.info("Gathering process info...")
    allps = {}
    openfiles = {}
    nslookup = {}
    dt = datetime.datetime.fromtimestamp
    for p in psutil.process_iter():
        try:
            if (len(p.cmdline) > 0):
                myps = {
                    "exe": p.exe,
                    "status": str(p.status),
                    "cmdline": " ".join(p.cmdline),
                    "user": p.username,
                    "memory": p.get_memory_percent(),
                    "create_time": dt(int(p.create_time)),
                    "uid": p.uids.effective,
                    "gids": p.gids.effective,
                    "fd_count": p.get_num_fds(),
                    "thread_count": p.get_num_threads(),
                }
                try:
                    o = sorted(set(
                               [ofile.path for ofile in p.get_open_files()]))
                    openfiles[p.pid] = o
                    myps["open_file_count"] = len(o)
                    myps["open"] = []
                    myps["open_fs"] = []
                except:
                    openfiles[p.pid] = []
                    myps["open_file_count"] = 0
                    myps["open"] = []
                    myps["open_fs"] = []
                try:
                    c, nslookup = sanitize_conns(
                        [[conn.local_address, conn.remote_address]
                            for conn in p.get_connections()], nslookup)
                    myps["connections"] = c
                except:
                    myps["connections"] = []
                try:
                    i = p.get_io_counters()
                    myps["read_count"] = i.read_count
                    myps["write_count"] = i.write_count
                    myps["read_bytes"] = i.read_bytes
                    myps["write_bytes"] = i.write_bytes
                except:
                    myps["read_count"] = 0
                    myps["write_count"] = 0
                    myps["read_bytes"] = 0
                    myps["write_bytes"] = 0
                l.info(("Processed pid: {} '{}' has " +
                        "open {} files, {} connections"
                        ).format(p.pid,
                                 myps["cmdline"][:25],
                                 myps["open_file_count"],
                                 len(myps["connections"]),
                                 ))
                allps[p.pid] = myps

        except:
            pass
    mountcache = {}
    execache = {}
    for pid in sorted(allps.keys()):
        if (allps[pid]["status"] == str(psutil.STATUS_RUNNING) or
            allps[pid]["status"] == str(psutil.STATUS_SLEEPING) or
            allps[pid]["status"] == str(psutil.STATUS_STOPPED) or
            allps[pid]["status"] == str(psutil.STATUS_TRACING_STOP) or
            allps[pid]["status"] == str(psutil.STATUS_WAKING)) and \
           (allps[pid]["open_file_count"] > 0):
            for f in openfiles[pid]:
                mountcache[f] = None
            exe = allps[pid]["exe"]
            if exe is not None and len(exe) > 0:
                execache[exe] = None
                allps[pid]["exe_fs"] = None
    mountcache = find_file_mounts(mountcache)
    execache = find_file_mounts(execache)
    for pid in sorted(allps.keys()):
        p = allps[pid]
        for f in openfiles[pid]:
            mountdevice_set = set()
            if f in mountcache:
                mountdevice = mountcache[f]
                if mountdevice is not None:
                    p["open"].append({"path": f, "fs": mountdevice})
                    mountdevice_set.add(mountdevice)
            p["open_fs"] = list(mountdevice_set)
        if "exe_fs" in p:
            exe = p["exe"]
            if exe in execache:
                p["exe_fs"] = execache[exe]
    #return allps, nslookup
    return allps


def df_parser(dfcache, dfout, dferr, filelist):
    # /usr/xpg4/bin/df
    dprint = debugprint(log_level="NODEBUG")
    mycache = {}
    mounts = deque()
    for line in dferr:
        dmsg = dprint()
        line = str(line.strip())
        re_str = '''df: [`(](.+)[')]:? .*'''
        dmsg += ["Input: '{}'".format(line),
                 "Regex: /{}/".format(re_str)]
        m = re.match(re_str, line)

        if m:
            path = m.group(1).strip()
            dmsg.append("match: Good found '{}'".format(path))
            dmsg.append("set: mycache[{}] = '{}'".format(
                        path, "error:/not/found"))
            mycache[path] = "error:/not/found"
        else:
            dmsg.append("match: Bad match")
        dmsg = dprint(dmsg, "dferr")
    #
    for line in dfout:
        dmsg = dprint()
        line = str(line.strip())
        re_str = '''([^ ].*[^ ])\s+[0-9]+''' + \
                 '''\s+[0-9]+\s+[0-9]+\s+([''' + \
                 '''0-9]+[%]|\s[-])\s.*'''
        dmsg += ["Input: '{}'".format(line),
                 "Regex: /{}/".format(re_str)]
        m = re.match(re_str, line)
        if m:
            mount = m.group(1).strip()
            mounts.append(mount)
            dmsg.append("match: Good found '{}'".format(mount))
            dmsg.append("set: mounts.append('{}')".format(mount))
        else:
            dmsg.append("match: Bad match")
        dmsg = dprint(dmsg, "dfout")
    #
    for f in filelist:
        if f not in mycache:
            try:
                mycache[f] = mounts.popleft()
            except:
                mycache[f] = None
    return dict(dfcache.items() + mycache.items())


def find_file_mounts(files, retry=2):
    reterr = []
    retout = []
    df_cache = {}
    filelist = files
    df_cmd = ["/bin/df", "-P"]
    ostype = os.uname()[0]
    if ostype == "SunOS":
        df_cmd = ["/usr/xpg4/bin/df", "-P"]
    for f in files:
        df_cache[f] = None
    filelist = df_cache.keys()
    for filebatch in [filelist[_:_ + 100]
                      for _ in range(0, len(filelist), 100)]:
        df = Command(df_cmd + filebatch)
        if df.run(maxtime=45) is not None:
            retout = df.output
            reterr = df.errput
            df_cache = df_parser(df_cache, retout, reterr, filebatch)
        else:
            for path in filebatch:
                df_cache[path] = None
    returndict = {}
    for f in files:
        if f in df_cache:
            returndict[f] = df_cache[f]
        else:
            returndict[f] = None
    return returndict


def find_device_fstype(device):
    for p in psutil.disk_partitions(all=True):
        if (p.device == device):
            return p.fstype
    return "unknown"


def sanitize_conns(connection_pairs, nslookup):
    sanitized_pairs = []
    for connection_pair in connection_pairs:
        src_conn = connection_pair[0]
        dst_conn = connection_pair[1]
        try:
            src_ip = str(netaddr.IPAddress(src_conn[0]).ipv4())
        except:
            src_ip = str(netaddr.IPAddress(src_conn[0]))
        '''
        if src_ip not in nslookup:
            src_name = timeout(
                fetch_dns, (src_ip,), timeout_duration=5, default=src_ip)
            if src_name != src_ip:
                nslookup[src_ip] = src_name
        '''
        src_port = src_conn[1]
        src_socket = "%s:%s" % (src_ip, src_port)
        dst_socket = None
        if (len(dst_conn) > 1):
            try:
                dst_ip = str(netaddr.IPAddress(dst_conn[0]).ipv4())
            except:
                dst_ip = str(netaddr.IPAddress(dst_conn[0]))
            '''
            if dst_ip not in nslookup:
                dst_name = timeout(
                    fetch_dns, (dst_ip,), timeout_duration=5, default=dst_ip)
                if dst_name != dst_ip:
                    nslookup[dst_ip] = dst_name
            '''
            dst_port = dst_conn[1]
            dst_socket = "%s:%s" % (dst_ip, dst_port)
        sanitized_pairs.append([src_socket, dst_socket])
    return sanitized_pairs, nslookup





