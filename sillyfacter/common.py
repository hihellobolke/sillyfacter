from __future__ import print_function
from __future__ import absolute_import
import os
import re
import subprocess
import threading
import logging
import socket
import inspect
import tempfile
import platform
#from common import *

MODULEFILE = re.sub('\.py', '',
                            os.path.basename(inspect.stack()[0][1]))


def debugprint(log_level=None):
    def dprint(lines=[], module=""):
        if type(lines) is not list:
            lines = [lines]
        if len(module) != 0:
            module = "[{}]".format(module)
        if len(lines) == 0:
            print("{}:".format(log_level), module, "-" * 40)
        else:
            for line in lines:
                print("{}:".format(log_level), module, line)
        return []

    def noop(a=[], b=""):
        return []

    if log_level == "DEBUG":
        return dprint
    else:
        return noop


def timeout(func, args=(), kwargs={},
            timeout_duration=10, default=None, log=None):
    """This function will spawn a thread and run the given function
    using the args, kwargs and return the given default value if the
    timeout_duration is exceeded.
    """
    class InterruptableThread(threading.Thread):

        def __init__(self):
            threading.Thread.__init__(self)
            self.result = default

        def run(self):
            self.result = func(*args, **kwargs)
    try:
        if log:
            log.info("Starting tiemoutthread for '{}' timeout in {}s".format(
                func.__name__, timeout_duration))
        it = InterruptableThread()
        it.start()
        it.join(timeout_duration)
        if it.isAlive():
            return it.result
        else:
            return it.result
    except:
        if log:
            log.warning("Exception occurred in timerthread for '{}'".format(
                func.__name__))
        return default


def _execute(cmd, stdout=None, stderr=None):
    retval = None
    if stderr is None:
        stderr = stdout
    try:
        proc = subprocess.Popen(cmd,
                                universal_newlines=True,
                                stdout=stdout,
                                stderr=stderr)
        retval = proc.wait()
    except:
        pass
        #raise
    return retval


def _read_unlink_handle(fh, fn):
    retval = []
    try:
        with os.fdopen(fh) as fd:
            fd.seek(0)
            retval = fd.readlines()
    except:
        pass
    finally:
        try:
            os.unlink(fn)
        except:
            pass
    return retval


class Command(object):
    def __init__(self, cmd, log=False):
        self.cmd = cmd
        self.process = None
        self.output = []
        self.errput = []
        self.errfile_handle, self.errfile_name = tempfile.mkstemp()
        self.outfile_handle, self.outfile_name = tempfile.mkstemp()

    def run(self, maxtime=30):
        self.retval = timeout(_execute,
                              args=(self.cmd,
                                    self.outfile_handle,
                                    self.errfile_handle),
                              timeout_duration=maxtime)
        self.output = _read_unlink_handle(self.outfile_handle,
                                          self.outfile_name)

        self.errput = _read_unlink_handle(self.errfile_handle,
                                          self.errfile_name)
        return self.retval


def fetch_dns(ip="127.0.0.1"):
    try:
        name = socket.gethostbyaddr(str(ip))[0]
    except:
        if re.match('^127\.[.0-9]*$', ip):
            name = "localhost"
        else:
            name = ip
    return name


def importer(modules=[]):
    ldict = {"step": MODULEFILE + "/" + inspect.stack()[0][3],
             "hostname": platform.node().split(".")[0]}
    l = logging.LoggerAdapter(fetch_lg(), ldict)
    #
    fetchable = {"custom": {}}
    for m in modules:
        try:
            fetchable["custom"][m] = \
                __import__("sillyfacter.custom.{}".format(m),
                           fromlist=[m],
                           level=0)
        except Exception as _:
            l.exception("Import exception for custon module 'custom/{}' " +
                        ": {}".format(m, _))
            try:
                fetchable[m] = __import__("sillyfacter.{}".format(m),
                                          fromlist=[m],
                                          level=0)
            except Exception as _:
                l.exception("Import exception for module " +
                            "'{}': {}".format(m, _))
                l.error("Import failure for module '{}'".format(m))
            else:
                l.info("Import success for module '{}'".format(m))
        else:
            l.info("Import success for  module 'custom/{}'".format(m))
    return fetchable


def fetcher(fetchable={}):
    ldict = {"step": MODULEFILE + "/" + inspect.stack()[0][3],
             "hostname": platform.node().split(".")[0]}
    l = logging.LoggerAdapter(fetch_lg(), ldict)
    #
    fetched = {}
    for modulename, moduleobj in fetchable.iteritems():
        if modulename is not "custom":
            try:
                fetched[modulename] = getattr(moduleobj, "fetch")()
            except Exception as _:
                l.exception("fetch failure for module " +
                            "{}, {}".format(modulename, _))
            else:
                l.info("fetch success for module {}".format(modulename))
        else:
            if "custom" not in fetched:
                fetched["custom"] = {}
            for modulename, moduleobj in fetchable["custom"].iteritems():
                try:
                    fetched["custom"][modulename] = \
                        getattr(moduleobj, "fetch")()
                except Exception as _:
                    l.exception("fetch failure for module " +
                                "{}, {}".format(modulename, _))
                else:
                    l.info("fetch success for module {}".format(modulename))
    return fetched, fetchable


def fetchprocessor(modules=[]):
    return fetcher(importer(modules))


def fetch_lg(name=None):
    return logging.getLogger("sillyfacter")


def setup_logger(name=None,
                 logfile=None,
                 console=True,
                 level=60,
                 ):
    log = fetch_lg()
    mylevel = 60 - level*20
    if mylevel < 10:
        log.setLevel(logging.DEBUG)
    elif mylevel >= 60:
        console = False
        log.setLevel(logging.CRITICAL)
    else:
        log.setLevel(mylevel)
    #
    if logfile is not None:
        fh = logging.FileHandler(file)
        fh.setLevel(logging.DEBUG)
        fmtf = logging.Formatter(
            '%(asctime)s - %(name)s ' +
            '%(hostname)-16s %(levelname)-8s ' +
            '@%(step)-30s %(message)s')
        fh.setFormatter(fmtf)
        log.addHandler(fh)
    #
    if console is True:
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        fmtc = logging.Formatter(
            '%(asctime)s - %(name)s ' +
            '%(hostname)-16s %(levelname)-8s ' +
            '@%(step)-30s %(message)s')
        ch.setFormatter(fmtc)
        log.addHandler(ch)
    return log
