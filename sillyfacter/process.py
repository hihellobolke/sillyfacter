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
import string
import stat
from collections import deque
from .common import *
import sillyfacter.config


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
                    "exe": ''.join(s for s in p.exe if s in string.printable),
                    "status": str(p.status),
                    "cmdline": " ".join(p.cmdline),
                    "user": p.username,
                    "memory_percent": p.get_memory_percent(),
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
                    myps["open_files"] = set()
                    myps["open_fs"] = []
                except:
                    openfiles[p.pid] = []
                    myps["open_file_count"] = 0
                    myps["open"] = []
                    myps["open_files"] = set()
                    myps["open_fs"] = []
                try:
                    c, nslookup = sanitize_conns(
                        [[conn.local_address, conn.remote_address]
                            for conn in p.get_connections()], nslookup)
                    myps["connection"] = c
                except:
                    myps["connection"] = []
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
                                 len(myps["connection"]),
                                 ))
                allps[p.pid] = myps

        except:
            if sillyfacter.config.DEBUG:
                l.exception("")
    mountcache = {}
    execache = {}
    for pid in sorted(allps.keys()):
        """if (allps[pid]["status"] == str(psutil.STATUS_RUNNING) or
            allps[pid]["status"] == str(psutil.STATUS_SLEEPING) or
            allps[pid]["status"] == str(psutil.STATUS_STOPPED) or
            allps[pid]["status"] == str(psutil.STATUS_TRACING_STOP) or
            allps[pid]["status"] == str(psutil.STATUS_WAKING)) and \
           (allps[pid]["open_file_count"] > 0):
            pass
        """
        for f in openfiles[pid]:
            mountcache[f] = None
        exe = allps[pid]["exe"]
        if exe is not None and len(exe) > 0:
            execache[exe] = None
            allps[pid]["exe_fs"] = None
    mountcache = find_file_mounts(mountcache, log=l)
    execache = find_file_mounts(execache, log=l)
    for pid in sorted(allps.keys()):
        p = allps[pid]
        if "exe_fs" in p:
            exe = p["exe"]
            if exe in execache:
                p["exe_fs"] = execache[exe]
        for f in openfiles[pid]:
            mountdevice_set = set()
            openfiles_set = set()
            if f in mountcache:
                mountdevice = mountcache[f]
                if mountdevice is not None:
                    p["open"].append({"path": f, "fs": mountdevice})
                    mountdevice_set.add(mountdevice)
                    openfiles_set.add(f)
            p["open_fs"] = list(mountdevice_set)
            p["open_files"] = list(openfiles_set)
            if "exe" in p and p["exe"] is not None:
                _ = p["open_files"] + [p["exe"]]
                p["open_files"] = list(set(_))
                p["open_file_count"] = len(p["open_files"])
            if "exe_fs" in p and p["exe_fs"] is not None:
                _ = p["open_fs"] + [p["exe_fs"]]
                p["open_fs"] = list(set(_))
            if sillyfacter.config.DEBUG:
                l.debug("Pid: {} Files: {}".format(pid, p["open"]))
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
                raise
                mycache[f] = None
    return dict(dfcache.items() + mycache.items())


def find_file_mounts(files, retry=2, log=None):
    df_cache = {}
    returndict = {}
    for f in files:
        df_cache[f] = None
    filelist = df_cache.keys()
    #
    ostype = os.uname()[0]
    if ostype == "SunOS":
        df_cmd = ["/usr/xpg4/bin/df", "-P"]
    elif ostype == "Linux":
        df_cmd = None
        returndict = _linux_use_stat(filelist, log=log)
    else:
        df_cmd = ["/bin/df", "-P"]
    if df_cmd:
        df_cache = _run_df(filelist, df_cmd)
        for f in files:
            if f in df_cache:
                returndict[f] = df_cache[f]
            else:
                returndict[f] = None
    return returndict


def _run_df(filelist, df_cmd):
    df_cache = {}
    reterr = []
    retout = []
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
    return df_cache


def _linux_use_stat(f, log=None):
    devnum_cache = _devicenum_cache(log=log)
    dev_cache = {}
    returndict = {}
    unknown_paths = []
    unknown_cache = {}
    for path in f:
        try:
            blk = os.stat(path)[stat.ST_DEV]
            dev_major = os.major(blk)
            dev_minor = os.minor(blk)
            dn = "{}:{}".format(dev_major, dev_minor)
            if dn in dev_cache:
                returndict[path] = dev_cache[dn]
            elif dn in devnum_cache:
                dev_cache[dn] = devnum_cache[dn]
                returndict[path] = dev_cache[dn]
            else:
                unknown_paths.append(path)
        except Exception as _:
            if sillyfacter.config.STRICT:
                raise
            if sillyfacter.config.DEBUG:
                dp = debugprint()
                dp("Error in stat of '{}' exception is '{}'".
                   format(path, _), "_linux_use_stat")
            if log:
                log.error("Stat failed for path: {}".format(path))
            returndict[path] = None
    if len(unknown_paths) > 0:
        unknown_cache = _run_df(unknown_paths, df_cmd=["/bin/df", "-P"])
        returndict = dict(returndict.items() + unknown_cache.items())
    return returndict


def _cat(f):
    l = []
    with open(f, "r") as g:
        for _ in g.readlines():
            l.append(_.strip())
    return l


def _devicenum_cache(log=None):
    dev_cache = {}
    #
    if os.path.exists("/proc/mounts"):
        for i in _cat("/proc/mounts"):
            mount_line = i.split()
            mount_device = mount_line[0]
            mount_point = mount_line[1]
            #mount_fstype = mount_line[2]
            try:
                blk = os.stat(mount_point)[stat.ST_DEV]
                dev_major = os.major(blk)
                dev_minor = os.minor(blk)
                dn = "{}:{}".format(dev_major, dev_minor)
                dev_cache[dn] = mount_device
            except Exception as _:
                if sillyfacter.config.STRICT:
                    raise
                if sillyfacter.config.DEBUG:
                    dp = debugprint()
                    dp("Error in stat of '{}' exception is '{}'".
                       format(mount_point, _), "_devicenum_cache")
                if log:
                    log.error("Stat failed for path: {} ({})".format
                              (mount_point, mount_device))
                pass
    #
    if os.path.exists("/proc/partitions"):
        for i in _cat("/proc/partitions"):
            if len(i) > 0 and re.match('\d+', i[0]):
                dev = i.split()
                dev_cache["{}:{}".format(dev[0], dev[1])] = "/dev/" + dev[-1]
    # this is never needed now
    if True is False and os.path.exists("/proc/fs/nfsfs/servers") and \
            os.path.exists("/proc/fs/nfsfs/volumes"):
        nfsfs_volumes = {}
        nfsfs_servers = {}
        for i in _cat("/proc/fs/nfsfs/volumes")[1:]:
            if len(i) > 0:
                dev_num = i.split()[3]
                server_id = i.split()[1]
            if re.match(".+:.+", dev_num):
                nfsfs_volumes[dev_num] = server_id
        for i in _cat("/proc/fs/nfsfs/servers")[1:]:
            if len(i) > 0:
                servername = i.split()[-1]
                server_id = i.split()[1]
            if re.match(".+:.+", dev_num):
                nfsfs_servers[server_id] = servername
        for dev_num in nfsfs_volumes:
            server_id = nfsfs_volumes[dev_num]
            try:
                dev_cache[dev_num] = "nfs://" + nfsfs_servers[server_id]
            except:
                if sillyfacter.config.STRICT:
                    raise
                pass
    #
    return dev_cache


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






