from __future__ import print_function
from __future__ import absolute_import
import os
import re
import logging
import platform
import inspect
import pymongo
import json
from .json import fetch2json
from ..common import *

MODULEFILE = re.sub('\.py', '',
                            os.path.basename(inspect.stack()[0][1]))


def output(modules=[], out='mongodb://localhost/sillyfacter_db'):
    ldict = {"step": MODULEFILE + "/" + inspect.stack()[0][3],
             "hostname": platform.node().split(".")[0]}
    l = logging.LoggerAdapter(fetch_lg(), ldict)
    #
    fetched, fetchable = fetchprocessor(modules)
    fetchobj = fetch2json(fetched, fetchable)
    fetchobj["_id"] = fetchobj["_scan_id"]
    return_dict = {"status": "Save failed",
                   "returncode": 1,
                   "url": out}
    coll, db, conn = _collection(dburl=out)
    retstr, returnval = None, None
    if coll is not None:
        try:
            docid = coll.save(fetchobj, safe=True)
            return_dict["status"] = "Save success"
            return_dict["_info"] = {}
            return_dict["_info"]["_id"] = docid
            return_dict["_info"]["collection"] = coll.name
            return_dict["_info"]["db"] = db.name
            return_dict["_info"]["host"] = conn.host
            return_dict["_info"]["port"] = conn.port
        except Exception as ex:
            l.exception("Unable to save data in collection: {}".format(ex))
            retval = 1
        else:
            l.info("Saved data with _id as '{}'".format(docid))
            return_dict["returncode"] = 0
            retval = 0
        finally:
            conn.close()
    retstr = json.dumps(return_dict,
                        sort_keys=True,
                        indent=4,
                        separators=(',', ': '))
    return retstr, retval


def _collection(dburl='mongodb://localhost/sillyfacter_db'):
    ldict = {"step": MODULEFILE + "/" + inspect.stack()[0][3],
             "hostname": platform.node().split(".")[0]}
    l = logging.LoggerAdapter(fetch_lg(), ldict)
    if dburl is not None:
        pass
    else:
        dburl = 'mongodb://localhost/sillyfacter_db'
    try:
        conn = pymongo.MongoClient(dburl)
    except Exception as ex:
        l.exception("Connection to '{}' failed: {}".format(dburl, ex))
        coll = None
        db = None
        conn = None
    else:
        try:
            db = conn.get_default_database()
        except:
            db = conn["sillyfacter_db"]
        coll = db["sillyfacter"]
    return coll, db, conn
