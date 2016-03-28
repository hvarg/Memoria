#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys#, os, getopt
#import json, re, copy

replaces = [('{',' { '), ('}',' } '),  ('[',' [ '), (']',' ] '),
            (';',' ; '), (',',' , ')]
url_repl = [('(',' ( '), (')', ' ) '), ('.',' . ')]
letters  = "abcdefghijklmnopqrstuvwxyz"

def find_par(alist, start, p=('{', '}') ): #if alist[start] == key[1]
    c = 0
    for i in range(start+1, len(alist)):
        key = alist[i]
        if key == p[0]: c += 1
        elif key == p[1]:
            if c == 0: return i
            else: c -= 1
    return -1

############################### The Query Class ###############################
class Query:
    def __init__(self, raw_str):
        #Normalize query TODO: improve me
        self.raw = ''
        for s in raw_str.split():
            if s[0] != '<':
                for a,b in url_repl:
                    s = s.replace(a,b)
            self.raw += s + ' '
        for a, b in replaces:
            self.raw = self.raw.replace(a,b)
        self.raw = ' '.join(self.raw.split())
        self.lower = self.raw.lower()
        #Check query type
        first_brack = self.lower.find('{')
        last_brack  = find_par(self.lower, first_brack)
        head = self.lower[:first_brack]
        if 'select ' in head:
            self.head = self.raw[:head.find('select')]
        elif 'construct ' in head:
            self.head = self.raw[:head.find('construct')]
        else:
            raise ValueError, 'Query type is not supported'
        self.qarg  = self.raw[len(self.head):first_brack]
        self.where = self.raw[first_brack:last_brack+1]
        self.tail  = self.raw[1+last_brack:]
#        print 'head:', self.head
#        print 'qarg:', self.qarg
#        print 'wher:', self.where
#        print 'rail:', self.tail
        if self.qarg == '' or self.where == '':
            raise ValueError, '--'
        self.letter_index = 0

    def get_triples(self):
        triple = []
        option = []
        litems = self.where.lower().split()
        items  = self.where.split()

        def rec_search(litems, items, stack=None):
            triple = []
            option = []
            if stack == None: stack = []
            i = 0
            while i < len(litems):
                t = litems[i]
                if t == '{':
                    j = find_par(litems, i)
                    tr, op  = rec_search(litems[i+1:j], items[i+1:j])
                    triple += tr
                    option += op
                    i = j
                elif t == 'optional'and litems[i+1] == '{':
                    j = find_par(litems, i+1)
                    tr, op  = rec_search(litems[i+2:j], items[i+2:j])
                    option += tr
                    i = j
                elif t == 'union' and litems[i+1] == '{':
                    j = find_par(litems, i+1)
                    tr, op  = rec_search(litems[i+2:j], items[i+2:j])
                    triple += tr
                    option += op
                    i = j
                elif t in ['graph', 'service'] and litems[i+2] == '{': #SERVICE?
                    j = find_par(litems, i+2)
                    tr, op  = rec_search(litems[i+3:j], items[i+3:j])
                    triple += tr
                    option += op
                    i = j
                elif t == 'filter':
                    if litems[i+1] == '(':
                        i = find_par(litems, i+1, ('(',')'))
                    elif litems[i+2] == '(':
                        i = find_par(litems, i+2, ('(',')'))
                elif t == ';':
                    a, b = stack.pop(), stack.pop()
                    triple.append( (stack[-1], b, a) )
                elif t == ',':
                    a = stack.pop()
                    triple.append( (stack[-1], stack[-2], a) )
                elif t == '.':
                    triple.append( tuple(stack) )
                    stack = []
                elif t == '[':
                    var_name = '?_' + letters[self.letter_index % 26]
                    self.letter_index += 1
                    stack.append( var_name )
                    j = find_par(litems,i,('[',']'))
                    if j-i > 1:
                        tr, op = rec_search(litems[i+1:j],items[i+1:j], stack=[var_name])
                    triple += tr
                    option += op
                    i = j
                else:
                    stack.append(items[i])
                i += 1
            if len(stack) == 3:
                triple.append( tuple(stack) )
            elif len(stack) != 0:
#                print>>sys.stderr, "WARNING: Stack not empty:", stack
                raise ValueError, "WARNING: Stack not empty: "+str(stack)
            return triple, option

        return rec_search(litems[1:-1], items[1:-1])

###############################################################################

################################ Main Function ################################
if __name__ == '__main__':
    files = sys.argv[1:]
    for f in files:
        try: l = open(f, 'r')
        except IOError: print>>sys.stderr, "No se puede abrir el archivo", f
        else:
            with l: content = l.read().strip()
#            print f
            q = Query(content)
            try:
                t, o = q.get_triples()
            except ValueError, e:
                print f, e
#            print 'TRIPLES:'
#            for i in t: print '\t',i
#            print 'OPTIONALS:'
#            for i in o: print '\t',i
#            print ''
