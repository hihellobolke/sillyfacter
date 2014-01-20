#!/usr/bin/env python

# Copyright 2012-2013, Gautam R Singh
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# -------------------------------------------------------------------- #
# 01.01.2014 - release to github - g@ut.am
# -------------------------------------------------------------------- #

from __future__ import print_function
import sys
import os
import platform
import time
import logging
import inspect
import argparse
import pprint
import re

sys.path.append(os.path.dirname(os.path.realpath(__file__)))


import sillyfacter.common

DEBUG = False
MODULEFILE = re.sub('\.py', '',
                            os.path.basename(inspect.stack()[0][1]))


if __name__ == '__main__':
    hostname = platform.node().split(".")[0]
    scan_time = int(time.time())
    parser = argparse.ArgumentParser(
        description='Sillyfacter fetches facts about the state of the ' +
                    'system. Gathers process, open file, socket info ' +
                    'and then outputs a JSON (currently). Designed for ' +
                    'dependency mappings.')
    parser.add_argument('--modules', type=str,
                        help='comma seperated list of modules ' +
                             'to be executed. Default list is ' +
                             '"process,network,user,os,fi' +
                             'lesystem".',
                        default="process,user,network,os,filesystem")
    parser.add_argument('--out', type=str,
                        help='[NOT IMPLEMENTED] ' +
                             'URL for the backend database (neo4j/mongo) ' +
                             'or a file to write json output to. If nothing ' +
                             'is supplied it dumps JSON to stdout',
                        default=None)
    parser.add_argument('--log', type=str,
                        help='file to write logs to, otherwise logs are ' +
                        'written to console',
                        default=None)
    parser.add_argument('--verbose', '-v', action='count',
                        help='For higher verbosity use multiple "-v" options',
                        default=0)
    parser.add_argument('--scan',
                        choices=('auto', 'new', 'last'),
                        help='[NOT IMPLEMENTED] ' +
                             'choose the scan type, usually "auto" ' +
                             'is the best.  [auto]', default='auto')
    parser.add_argument('--raw',
                        help='[NOT IMPLEMENTED] ' +
                             'Use raw output, default is false',
                        action='store_true')
    parser.add_argument('--version', action='version',
                        version="0.0")

    args = parser.parse_args()
    #
    lg = sillyfacter.common.setup_logger(level=args.verbose,
                                         logfile=args.log)
    ldict = {"step": "main",
             "hostname": platform.node().split(".")[0]}
    l = logging.LoggerAdapter(sillyfacter.common.fetch_lg(), ldict)
    #
    fetchable = {}
    modules = args.modules.split(',')
    #
    if args.out is None or \
            re.match('^[/a-z0-9].*\.json', args.out, re.IGNORECASE):
        outmodule = "json"
        output = None
        try:
            l.info("Importing output filter '{}'".format(outmodule))
            outmodule = __import__("sillyfacter.output.{}".format(outmodule),
                                   fromlist=[outmodule])
            output = getattr(outmodule, "fetchprocessor")(modules)
        except:
            raise
        else:
            print("{}".format(output))
    l.info("Bye bye")
