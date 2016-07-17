#!/usr/bin/env python
# -*- coding: utf-8 -*-
import urllib, urllib2
import sys, getopt
from SPARQLWrapper import SPARQLWrapper

get = lambda: 'GET'
opener = urllib2.build_opener(urllib2.HTTPHandler)
help_string = """Uso: sparql_query [opciones] archivos
Envia las consultas al endpoint seleccionado.

Opciones:
    -e, --endpoint <url>   Endpoint, (por defecto 'http://bio2rdf.org/sparql')
    -f, --format <format>  Formato, (por defecto 'text/plain')
    -o, --output <file>    Salida, (por defecto '/dev/stdout')
    -h, --help             Muestra esta ayuda y termina."""

def send_query(query, endpoint, f):
    params  = urllib.urlencode( {'query': query} )
    request = urllib2.Request(endpoint + '?' + params)
    request.add_header('Accept', f)
    request.get_method = get
    result = opener.open(request)
    return result.read()

if __name__ == '__main__':
    endpoint    = 'http://bio2rdf.org/sparql'
    format_type = 'text/plain'
    output      = '/dev/stdout'

    try: options, files = getopt.gnu_getopt(sys.argv[1:], 'e:f:o:h',
            ["endpoint=", "format=", "help", "output="])
    except Exception, e:
        print str(e)
        exit(-1)

    for opt, arg in options:
        if opt in ("--help", "-h"):         print help_string; exit(0)
        elif opt in ("--endpoint", "-e"):   endpoint    = arg
        elif opt in ("--output", "-o"):     output      = arg
        elif opt in ("--format", "-f"):     format_type = arg
    empty_file = open('empty_querys', 'a')
    error_file = open('error_querys', 'a')
    log_file   = open('sparql_qlog', 'a')

    with open(output, 'w') as out:
        for f in files:
            try: l = open(f, 'r')
            except IOError: print>>sys.stderr, "No se puede abrir el archivo", f
            else:
                i = 0
                for line in l:
                    i += 1
                    content = line.strip()
                    try:
                        result = send_query(content, endpoint, format_type)
                    except Exception, e:
                        error_file.write("%s (%d)\t%s\n" % (f, i, str(e)))
                        result = str(e) + '\n'
                        continue
                    if result[0] == '#':
                        empty_file.write("%s\t%d\n" % (f, i))
                    else:
                        log_file.write("%s (%d)\tDone\n" % (f, i))
                        out.write(result)
                l.close()
    empty_file.close()
    error_file.close()
