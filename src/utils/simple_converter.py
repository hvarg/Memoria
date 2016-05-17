#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
if __name__ == '__main__':
    files = sys.argv[1:]
    for f in files:
        try: infile = open(f, 'r')
        except IOError: print>>sys.stderr, "No se puede abrir el archivo", f
        else:
            mem = {}
            names = {}
            numbers = {}
            i = 0
            for line in infile:
                # a --b--> c
                a,b,c = line.split('\t')
                c = c[:-3]
                if not names.has_key(a):
                    names[a] = i
                    numbers[i] = a
                    i += 1
                if not names.has_key(c):
                    names[c] = i
                    numbers[i] = c
                    i += 1
                if not mem.has_key(names[a]):
                    mem[names[a]] = set()
                mem[names[a]].add(names[c])
            # Writing names:
            with open(f+'.names', 'w') as namesfile:
                for n in range(i):
                    namesfile.write(str(n)+' '+numbers[n]+'\n')
            with open(f+'.sg', 'w') as graphfile:
                for n in range(i):
                    graphfile.write(str(n)+':')
                    if mem.has_key(n):
                        for m in mem[n]:
                            graphfile.write(' '+str(m))
                    graphfile.write('\n')
            infile.close()
