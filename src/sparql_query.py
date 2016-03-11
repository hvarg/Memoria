#!/usr/bin/env python                                                           
# -*- coding: utf-8 -*-
import json
import urllib2
import urllib
import traceback
import sys
from SPARQLWrapper import SPARQLWrapper, JSON

def query(q, epr, f='application/json'):
    try:
        params = {'query': q}
        params = urllib.urlencode(params)
        #print(params)
        opener = urllib2.build_opener(urllib2.HTTPHandler)
        request = urllib2.Request(epr + '?' + params)
        request.add_header('Accept', f)
        request.get_method = lambda: 'GET'
        url = opener.open(request)
        return url.read()
    except Exception, e:
        print(epr)
        traceback.print_exc(file=sys.stdout)
        raise e

if __name__ == '__main__':
    print(sys.argv[1])
    with open(sys.argv[1], 'r') as q:
        content = q.read().strip()
#    result = urllib2.urlopen(sys.argv[2] + '?query=' + urllib.quote(content))
    result = query(content, sys.argv[2])
    jsonresults = json.loads(result)
    print(json.dumps(jsonresults))
