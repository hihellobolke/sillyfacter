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
    retval = {"status": "Save failed",
              "url": out}
    coll, db, conn = _collection(dburl=out)
    if coll is not None:
        try:
            docid = coll.save(fetchobj, safe=True)
            retval["status"] = "Save success"
            retval["_info"] = {}
            retval["_info"]["_id"] = docid
            retval["_info"]["collection"] = coll.name
            retval["_info"]["db"] = db.name
            retval["_info"]["host"] = conn.host
            retval["_info"]["port"] = conn.port
        except Exception as ex:
            l.exception("Unable to save data in collection: {}".format(ex))
        else:
            l.info("Saved data with _id as '{}'".format(docid))
        finally:
            conn.close()
    jsonstr = json.dumps(retval,
                         sort_keys=True,
                         indent=4,
                         separators=(',', ': '))
    return jsonstr


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
