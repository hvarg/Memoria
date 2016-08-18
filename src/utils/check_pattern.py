#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os, getopt, json, operator
import numpy as np
from datetime import datetime
from datetime import timedelta

help_string = """Uso: check_pattern.py archivos.json [...]
Genera un diccionario con los datos y patrones de las consultas.

Opciones:
    -r                      Recursivo.
    --session-dur           Especifica la duración de la sesión (en segundos).
    --ignore-describe       Ignora las consultas con describe.
    -h, --help              Muestra esta ayuda y termina."""


def diff_dates(date1, date2):
  return abs((date2-date1)).seconds

if __name__ == '__main__':
  SESSION_DUR = 300
  rec         = False
  ignore_desc = False
  try:
    options, files = getopt.gnu_getopt(sys.argv[1:], 'hr', 
        ["help", "session-dur=","ignore-describe"])
  except Exception,e:
    print>>sys.stderr, str(e)
    exit(-1)

  for opt, arg in options:
    if   opt in ("--help", "-h"):     print help_string; exit(0)
    elif opt == "--session-dur":      SESSION_DUR = int(arg)
    elif opt == "--ignore-describe":  ignore_desc = True
    elif opt == "-r":                 rec         = True

  session_dur = timedelta(seconds=SESSION_DUR)

  if rec:
    for f in files:
      if os.path.isdir(f):
        for new_file in os.listdir(f):
          files.append(f + '/' + new_file)

  ps = {}
  for f in files:
    if os.path.isdir(f): continue
    with open(f, 'r') as f:
      for line in f:
        js_d = json.loads(line)
        if ignore_desc and js_d['descr'] == True:
          continue
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
        if not ps[js_d['pattern']]['vars'].has_key(str(js_d['vars'])):
          ps[js_d['pattern']]['vars'][str(js_d['vars'])] = 0
        if not ps[js_d['pattern']]['lits'].has_key(str(js_d['lits'])):
          ps[js_d['pattern']]['lits'][str(js_d['lits'])] = 0
        if not ps[js_d['pattern']]['ua'].has_key(str(js_d['user-agent'])):
          ps[js_d['pattern']]['ua'][str(js_d['user-agent'])] = 0
        ps[js_d['pattern']]['uris'][str(js_d['uris'])]      += 1
        ps[js_d['pattern']]['vars'][str(js_d['vars'])] += 1
        ps[js_d['pattern']]['lits'][str(js_d['lits'])]  += 1
        ps[js_d['pattern']]['ua'][str(js_d['user-agent'])]  += 1
        ps[js_d['pattern']]['dates'].append(datetime.strptime(
          js_d['date'][:-6], '%d/%b/%Y:%H:%M:%S')) #FIXME
  results = {}
  for key in ps:
    results[key] = {}
    m = max([ps[key]['uris'][k] for k in ps[key]['uris']])
    results[key]['uris'] = float(m)/float(ps[key]['count'])
    m = max([ps[key]['vars'][k] for k in ps[key]['vars']])
    results[key]['vars'] = float(m)/float(ps[key]['count'])
    m = max([ps[key]['lits'][k] for k in ps[key]['lits']])
    results[key]['lits'] = float(m)/float(ps[key]['count'])
    diffs = []
    # Se calcula el tiempo entre consultas de las mismas sesiones, asumiendo que
    # cuando pasa un tiempo mayor a una hora son sesiones diferentes.
    last    = None
    s_count = 0
    for date in ps[key]['dates']:
      if last != None:
        rest = diff_dates(date, last)
        if rest < SESSION_DUR:
          diffs.append( rest )
          s_count += 1
      last = date
    if len(diffs) > 1:
      arr = np.array( diffs )
      results[key]['mean'] = np.mean(arr)
      results[key]['std']  = np.std(arr)
    else:
      results[key]['mean'] = -1
      results[key]['std']  = -1
    results[key]['sessions'] = s_count
    results[key]['count']    = ps[key]['count']
    results[key]['pattern']  = key

  sorted_keys = sorted([(key, ps[key]['count']) for key in ps],
      key=operator.itemgetter(1), reverse=True)

  with open('results.json', 'w') as out:
    for key, c in sorted_keys:
      print>>out, json.dumps(results[key])

  str_s_dur = str(session_dur)
  for key, c in sorted_keys:
    try:
      print "%d ocurrencias del patron: %s" % (c, key)
      print "\tUn %0.2f%% utilizó las mismas URIs" % (results[key]['uris']*100)
      print "\tUn %0.2f%% utilizó las mismas variables"%(results[key]['vars']*100)
      print "\tUn %0.2f%% utilizó los mismos literales"%(results[key]['lits']*100)
      if results[key]['mean'] != -1:
        print "\tLa media del tiempo transcurrido entre consultas fue de",
        print "%0.2f segundos (ds = %0.2f, %d sesiones (%0.2f%%))" % \
            (results[key]['mean'], results[key]['std'], results[key]['sessions'],
                100*results[key]['sessions']/float(c))
      else:
        print "\tTiempo entre consultas mayor a la duración de la sesión (%s)." %\
            (str_s_dur)
      print "\tSe utilizaron %d user-agent diferentes." % (len(ps[key]['ua']))
    except:
      print "Ocurrio un error imprimiendo", key
