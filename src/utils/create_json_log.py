#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys, os, getopt
import json, re

help_string = """Uso: create_json_log raw_query.txt *
Genera un diccionario con los datos y patrones de las consultas.

Opciones:
    -d                   Debug.
    --debug              Recursivo.
    --indent             Guarda los resultados con indentacion. 
    -h, --help           Muestra esta ayuda y termina."""

###############################################################################

re_limit   = re.compile(r'limit (\d+)', re.IGNORECASE)
re_offset  = re.compile(r'offset (\d+)', re.IGNORECASE)
re_prefix  = re.compile(r'prefix ([a-zA-Z0-9_]+:) (<[^<> ]*>)', re.IGNORECASE)
re_uri     = re.compile(r'(<[^<> ]*>)')
re_literal = re.compile(r'("[^"]*"|\d+|' + r"'[^']*')")
re_var     = re.compile(r'\?[a-zA-Z0-9_]+')

def get_pattern(raw):
  # Buscando Where
  i = len(raw) - 1
  init, end = 0, 0
  c = 0
  while (i >= 0):
    if (raw[i] == '}'):
      if (end == 0): end = i + 1;
      else: c += 1
    elif (raw[i] == '{'):
      if (c == 0):
        init = i
        break
      else: c -= 1
    i -= 1
  if (i == 0): IndexError("No se encontro WHERE.")
  pattern = raw[init:end]
  if not pattern:
    pattern = raw #test
  # Reemplazando prefijos
  prefixes = re_prefix.findall(raw[:init])
  if prefixes:
    for p, ur in prefixes:
      l = [m.end(0) for m in re.finditer(p, pattern)]
      for x in l:
        while pattern[x] not in [' ',')','}']: x += 1
        pattern = pattern[:x] + '>' + pattern[x:]
      pattern = re.sub(p, ur[:-1], pattern)
  # Determinando variables
  uris = re_uri.findall(pattern)
  if uris: pattern = re_uri.sub('_URI_', pattern)
  vars = re_var.findall(pattern)
  if vars: pattern = re_var.sub('_VAR_', pattern)
  lits = re_literal.findall(pattern)
  if lits: pattern = re_literal.sub('_LIT_', pattern)
  limits = re_limit.findall(raw[end-1:])
  if limits: limits = limits[0]
  else:      limits = None
  offsets = re_offset.findall(raw[end-1:])
  if offsets: offsets = offsets[0]
  else:       offsets = None
  return pattern, uris, vars, lits, limits, offsets

################################ Main Function ################################
if __name__ == '__main__':
  rec      = False
  debug    = False
  indent   = False

  try:
    options, files = getopt.gnu_getopt(sys.argv[1:], 'hr', 
        ["help", "debug", "indent"])
  except Exception,e:
    print str(e)
    exit(-1)

  for opt, arg in options:
    if   opt in ("--help", "-h"):   print help_string; exit(0)
    elif opt == "--indent":         indent    = True
    elif opt == "--debug":          debug     = True
    elif opt == "-r":               rec       = True
    
  if rec:
    for f in files:
      if os.path.isdir(f):
        for new_file in os.listdir(f):
          files.append(f + '/' + new_file)

  for f in files:
    dic = {}
    if os.path.isdir(f): continue
    try:
      l = open(f, 'r')
    except IOError:
      print>>sys.stderr, "No se puede abrir el archivo", f
    else:
      nline = 0
      for line in l:
        if debug: print "\r%s (%d)" % (f, nline+1), 
        sp = line.split('<sep>')
        if len(sp) != 7:
          print>>sys.stderr, sp[-1][:-1]
        else:
          ip, date, raw, _, user_agent, _, _ = sp
          if not dic.has_key(ip):
            dic[ip] = []
          current = {}
          current['date']       = date
          current['raw']        = raw
          current['user-agent'] = user_agent
          current['pattern'], current['uris'], current['variables'], \
              current['literals'], current['limit'], current['offset'] = \
              get_pattern(raw)
          if current['pattern']: dic[ip].append(current)
          else:
            print>>sys.stderr, "%s (%d): consulta sin Where." % (f, nline)
        nline += 1
      if debug: print '\r'
      l.close()

    for ip in dic:
      if len(dic[ip]) > 0:
        with open(ip + '.json', 'a') as out:
          if indent: print>>out, json.dumps(dic[ip], indent=2)
          else:
            for query in dic[ip]:
              print>>out, json.dumps(query)
