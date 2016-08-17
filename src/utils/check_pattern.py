#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, json
import numpy as np
from datetime import datetime

SESION_DUR = 100

def diff_dates(date1, date2):
  return abs((date2-date1)).seconds

if __name__ == '__main__':
  ps = {}
  for f in sys.argv[1:]:
    with open(f, 'r') as f:
      for line in f:
        js_d = json.loads(line)
        if not ps.has_key(js_d['pattern']): 
          ps[js_d['pattern']] = {}
          ps[js_d['pattern']]['count']  = 0
          ps[js_d['pattern']]['uris']   = {}
          ps[js_d['pattern']]['vars']   = {}
          ps[js_d['pattern']]['lits']   = {}
          ps[js_d['pattern']]['ua']     = {}
          ps[js_d['pattern']]['dates']  = []
        ps[js_d['pattern']]['count'] += 1
        if not ps[js_d['pattern']]['uris'].has_key(str(js_d['uris'])):
          ps[js_d['pattern']]['uris'][str(js_d['uris'])] = 0
        if not ps[js_d['pattern']]['vars'].has_key(str(js_d['variables'])):
          ps[js_d['pattern']]['vars'][str(js_d['variables'])] = 0
        if not ps[js_d['pattern']]['lits'].has_key(str(js_d['literals'])):
          ps[js_d['pattern']]['lits'][str(js_d['literals'])] = 0
        if not ps[js_d['pattern']]['ua'].has_key(str(js_d['user-agent'])):
          ps[js_d['pattern']]['ua'][str(js_d['user-agent'])] = 0
        ps[js_d['pattern']]['uris'][str(js_d['uris'])]      += 1
        ps[js_d['pattern']]['vars'][str(js_d['variables'])] += 1
        ps[js_d['pattern']]['lits'][str(js_d['literals'])]  += 1
        ps[js_d['pattern']]['ua'][str(js_d['user-agent'])]  += 1
        ps[js_d['pattern']]['dates'].append(datetime.strptime(
          js_d['date'][:-6], '%d/%b/%Y:%H:%M:%S')) #FIXME
  results = {}
  for key in ps:
    results[key] = []
    m = max([ps[key]['uris'][k] for k in ps[key]['uris']])
    results[key].append( float(m)/float(ps[key]['count']) )
    m = max([ps[key]['vars'][k] for k in ps[key]['vars']])
    results[key].append( float(m)/float(ps[key]['count']) )
    m = max([ps[key]['lits'][k] for k in ps[key]['lits']])
    results[key].append( float(m)/float(ps[key]['count']) )
    diffs = []
    # Se calcula el tiempo entre consultas de las mismas sesiones, asumiendo que
    # cuando pasa un tiempo mayor a una hora son sesiones diferentes.
    last  = None
    for date in ps[key]['dates']:
      if last != None:
        rest = diff_dates(date, last)
        if rest < SESION_DUR:
         diffs.append( rest )
      last = date
    if len(diffs) > 1:
      arr = np.array( diffs )
      results[key].append( np.mean(arr) )
      results[key].append( np.std(arr) )
    else:
      results[key].append(0)
      results[key].append(0)

  for key in ps:
    print "%d ocurrencias del patron: %s" % (ps[key]['count'], key)
    print "\tUn %0.2f%% utilizó las mismas URIs" % (results[key][0] *100)
    print "\tUn %0.2f%% utilizó las mismas variables" % (results[key][1] *100)
    print "\tUn %0.2f%% utilizó los mismos literales" % (results[key][2] *100)
    if results[key][3] != 0:
      print "\tLa media del tiempo transcurrido entre consultas fue de",
      print "%0.2f segundos (ds = %0.2f)" % tuple(results[key][3:])
    print "\tSe utilizaron %d user-agent diferentes." % (len(ps[key]['ua']))
