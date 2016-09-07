#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os, re
replaces = [('{',' { '), ('}',' } '), ('[',' [ '), (']',' ] '), ('=',' = '),
            (';',' ; '), (',',' , '), ('(',' ( '), (')',' ) '), ('.',' . ')]

bracks = {'(':')', '{':'}'}

def add_number(query):
  nv, nu, nl = [], [], []
  v = re.findall(r'_VAR_', query)
  u = re.findall(r'_URI_', query)
  l = re.findall(r'_LIT_', query)
  query = re.sub(r'_VAR_', ' %s ', query)
  for i, key in enumerate(v): nv.append( key[:-3] + str(i) + key[-1] )
  query = query % tuple(nv)
  query = re.sub(r'_URI_', ' %s ', query)
  for i, key in enumerate(u): nu.append( key[:-3] + str(i) + key[-1] )
  query = query % tuple(nu)
  query = re.sub(r'_LIT_', ' %s ', query)
  for i, key in enumerate(l): nl.append( key[:-3] + str(i) + key[-1] )
  query = query % tuple(nl)
  return query

def normalize(query):
  for a,b in replaces:
    query = query.replace(a,b)
  return ' '.join(query.split()).upper() #not lower

def mark(string, i, j=None):
  print string
  if not j:
    print ' '*i + '^'
  else:
    print ' '*i + '⎻'*(j-i)

def find_par(alist, start):
  c = 0
  for i in range(start+1, len(alist)):
    key = alist[i]
    if key == alist[start]: c += 1
    elif key == bracks[alist[start]]:
      if c == 0: return i
      else: c -= 1
  #mark(alist, start)
  raise IndexError("No se encontro par.")

def clean(query):
  if ('SELECT' in query) or ('#' in query): # or ('SELECT' in query):
    #return query
    raise NotImplementedError

  while 'FILTER' in query:
    s = query.find('FILTER')
    e = query[s+6:].find('(')
    if (e == -1):
      e = query[s+6:].find('{')
      e = find_par(query, e + s + 6) + 1
    else:
      e = find_par(query, e + s + 6) + 1
    query = query[:s] + '.' + query[e:]

  while 'BIND' in query:
    s = query.find('BIND')
    e = query[s+4:].find('(')
    e = find_par(query, e + s + 4) + 1
    query = query[:s] + '.' + query[e:]

  while 'VALUES' in query:
    s = query.find('VALUES')
    e = query[s+6:].find('{')
    e = find_par(query, e + s + 6) + 1
    query = query[:s] + '.' + query[e:]

  if 'GRAPH' in query:   query = re.sub(r'GRAPH [^ ]*', '', query)
  if 'SERVICE' in query: query = re.sub(r'SERVICE ?(SILENT ?)?[^ ]*', '', query)
  if 'MINUS' in query:   query = re.sub(r'MINUS', '', query)
  #Others filters
  new_query = []
  last_dot = False
  for item in query.split():
    if item not in ['OPTIONAL', 'UNION']: #Cosas que saltarse
      if item in ['{', '}', '.']:
        if not last_dot:
          new_query.append('.')
          last_dot = True
      else:
        last_dot = False
        if ':' in item: new_query.append('_E_')
        else: new_query.append( item )
  query = re.sub(r'@[^ ]*', '', ' '.join(new_query)).replace(' ^^ ', '^^')
  for item in query.split():
    if item[0] not in ['_', ',', '.', ';', 'A', '[', ']']:
      return ''
  return query

def make_graph(query):
  graph = {}
  varid = 0
  def graph_check(key):
    if not graph.has_key(key): graph[key] = []
  def get_var():
    i += 1
    return '_?' + str(i) + '_'
  def get_triple(alist, stack=[]):
    for i, item in enumerate(alist):
      l = len(stack)
      if item in ['.', ';', ',']:
        if l == 0: continue
        elif l == 3:
          graph_check(stack[0])
          graph_check(stack[2])
          graph[stack[0]].append(stack[2])
        else:
          print "Stack Error"
        if item == '.': stack = []
        if item == ';': stack = stack[:1]
        if item == ',': stack = stack[:2]
      elif item == '[':
        var = get_var()
        get_triple(alist[i+1:], [var])
        stack.append( var )
      elif item == ']':
        return
      else: stack.append( item )
  get_triple(query.split())
  return graph

def set_equal(graph, vs, us, ls):
  new_graph = {}
  eq = {}
  dc = {}
  tg = None
  for item in graph:
    n = int(item[2:-1])
    if item[1] == 'V': tg = vs
    if item[1] == 'U': tg = us
    if item[1] == 'L': tg = ls
    if not dc.has_key(tg[n]):
      dc[tg[n]] = item
    eq[item] = dc[tg[n]]
  for item in graph:
    if not new_graph.has_key(eq[item]):
      new_graph[eq[item]] = []
    for key in graph[item]:
      new_graph[eq[item]].append( eq[key] )
  return new_graph

def g_order(graph):
  return len(graph)

def g_max_odc(graph):
  m = 0
  for key in graph:
    if len(graph[key]) > m:
      m = len(graph[key])
  return m

def g_max_path(graph):
  def _mx(g, k):
    m = 0
    for v in g[k]:
      n = _mx(g, v)
      if n > m: m = n
    return m + 1
  M = 0
  for key in graph:
    N = _mx(graph, key)
    if N > M: M = N
  return M-1

if __name__ == '__main__':
  with open(sys.argv[1], 'r') as f:
    i = 0
    for line in f:
      try:
        query = add_number(line)
        query = normalize(query)
        print query
        query = clean(query)
        print query
        make_graph(query)
      except:
        print ''
#        print '!',query
      i += 1
      if i > 15 : break
