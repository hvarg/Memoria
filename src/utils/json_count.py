#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys, os, getopt
import json, re

help_string = """Uso: json_count -a <attr> [opciones] archivos
Revisa uno o más archivos json y cuenta el valor del atributo.

Opciones:
    -a, --attr <str>     Selecciona el atributo a contar.
    -e, --expr <str>     Filtra el resultado según la expresión regular.
    -r                   Recursivo.
    -h, --help           Muestra esta ayuda y termina."""

################################ Main Function ################################

if __name__ == '__main__':
    regex = None
    attr  = None
    rec   = False

    try: options, files = getopt.gnu_getopt(sys.argv[1:], 'a:hre:',
            ["attr=", "help", "regex="])
    except Exception,e:
        print str(e)
        exit(-1)

    for opt, arg in options:
        if   opt in ("--help", "-h"):   print help_string; exit(0)
        elif opt in ("--attr", "-a"):   attr   = arg
        elif opt in ("--expr", "-e"):   regex  = re.compile(arg)
        elif opt == "-r":               rec = True
        
    if not attr:
        print>>sys.stderr, "Debe ingresar un atributo."
        print>>sys.stderr, "--help para más información."
        exit(-1);

    count = {}

    if rec:
        for f in files:
            if os.path.isdir(f):
                for new_file in os.listdir(f):
                    files.append(f + '/' + new_file)

    for f in files:
        if os.path.isdir(f): continue
        try: l = open(f, 'r')
        except IOError: print>>sys.stderr, "No se puede abrir el archivo", f
        else:
            for line in l:
                try:
                    dict_line = json.loads(line)
                    value     = dict_line[attr]
                except:
                    print>>sys.stderr, "Error leyendo el atributo"
                    continue
                if regex:
                    m = regex.search(value)
                    if m: value = m.group()
                    else: print>>sys.stderr, "'%s' no match" % (value); continue
                if not count.has_key(value):
                    count[value] = 1
                else: count[value] += 1
    for key in count:
        print key, count[key]
