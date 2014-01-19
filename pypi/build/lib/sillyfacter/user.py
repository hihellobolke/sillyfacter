from __future__ import print_function
from __future__ import absolute_import
import psutil
import os
import platform
import re
import logging
import inspect
import datetime
from .common import *


MODULEFILE = re.sub('\.py', '',
                            os.path.basename(inspect.stack()[0][1]))


def fetch():
    ldict = {"step": MODULEFILE + "/" + inspect.stack()[0][3],
             "hostname": platform.node().split(".")[0]}
    l = logging.LoggerAdapter(fetch_lg(), ldict)
    #
    l.info("Gathering users info...")
    users = {}
    users["current"] = current_users()
    users["last"] = last_users()
    return users


def current_users():
    ldict = {"step": inspect.stack()[0][3],
             "hostname": platform.node().split(".")[0]}
    l = logging.LoggerAdapter(fetch_lg(), ldict)
    #
    l.info("Gathering logged in users...")
    host_users = []
    for item in psutil.get_users():
        user = item[0]
        term = item[1]
        host = item[2]
        host_users.append({"user": user,
                           "terminal": term,
                           "from": host})
    return host_users


def last_users(last=20):
    ldict = {"step": inspect.stack()[0][3],
             "hostname": platform.node().split(".")[0]}
    l = logging.LoggerAdapter(fetch_lg(), ldict)
    l.info("Gather users logged in 20 days")
    ret = []
    ostype = os.uname()[0]
    if ostype == "SunOS":
        last_cmd = ["/bin/last", "-a"]
    elif ostype == "Linux":
        last_cmd = ["/usr/bin/lastlog", "-t", "{}".format(last)]
    else:
        last_cmd = ["/usr/bin/last"]
    last = Command(last_cmd)
    if last.run(maxtime=5) is not None:
        output = last.output
        ret = last_parser(output, last=last)
    return ret


def last_parser(lastout, last=20):
    _log_level = "not_debug"
    dprint = debugprint(log_level=_log_level)
    last_users = []
    today = datetime.datetime.today()
    re_solaris = '([0-9a-z]+)\s+' + \
                 '.+' + \
                 '(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+' + \
                 '([a-z]{3})\s+' + \
                 '([0-9]+)\s+' + \
                 '([0-9][0-9]):([0-9][0-9]).*$'
    re_solaris = re.compile(re_solaris, re.IGNORECASE)
    ostype = os.uname()[0]
    if ostype == "Linux":
        last_users = [line.split()[0] for line in lastout[1:]]
    else:
        regx = re_solaris
        for line in lastout:
            dmsg = dprint()
            line = str(line.strip())
            dmsg += ["Input: '{}'".format(line)]
            m = regx.match(line)
            if m:
                user = m.group(1).strip()
                mm = m.group(3).strip()
                dd = int(m.group(4).strip())
                hour = m.group(5).strip()
                mins = m.group(6).strip()
                date_string = "{:02} {} {} {} {}".format(dd, mm, today.year,
                                                         hour, mins)
                date_format = "%d %b %Y %H %M"
                parsed_date = datetime.datetime.strptime(date_string,
                                                         date_format)
                if parsed_date > today:
                    date_string = "{:02} {} {} {} {}".format(dd, mm,
                                                             today.year - 1,
                                                             hour, mins)
                    parsed_date = datetime.datetime.strptime(date_string,
                                                             date_format)
                if parsed_date > (today - datetime.timedelta(days=20)):
                    last_users.append(user)
                dmsg.append("set: last_users.add({})".format(user))

            else:
                dmsg.append("match: Bad match")
            dmsg = dprint(dmsg, "lastuser")
            last_users = list(set(last_users))
    return last_users
    #
