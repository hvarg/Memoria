#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys, os, getopt
import json, re, copy
from Query import Query

help_string = """Uso: extract_query [opciones] archivos
Extrae las consultas de un log json y hace cambios para retornar los triples
consultados. 

Opciones:
    --to-ask            Transforma las consultas en ASK en vez de CONSTRUCT.
    --no-save           No guarda las consultas resultantes.
    --save-raw          Tambien guarda las consultas originales.
    --extension <str>   Especifica la extension (por defecto '.sparql').
    -V, --verbose       Muestra por salida estandar las consultas resultantes.
    -o, --output <file> Cambia la carpeta de salida predeterminada.
    -h, --help          Muestra esta ayuda y termina."""

################################ Main Function ################################
if __name__ == '__main__':
    verbose    = False
    save_raw   = False
    no_save    = False
    output_dir = "results"
    ext        = ".sparql"

    try: options, files = getopt.gnu_getopt(sys.argv[1:], 'o:hV',
            ["output=", "help", "verbose", "save-raw",
             "extension=", "no-save", "to-ask"])
    except Exception,e:
        print str(e)
        exit(-1)

    for opt, arg in options:
        if opt in ("--help", "-h"):       print help_string; exit(0)
        elif opt in ("--output", "-o"):   output_dir       = arg
        elif opt in ("--verbose", "-V"):  verbose          = True
        elif opt == "--save-raw":         save_raw         = True
        elif opt == "--no-save":          no_save          = True
        elif opt == "--to-ask":           to_ask           = True
        elif opt == "--extension":        ext              = arg

    try: 
        os.makedirs(output_dir)
    except OSError, e:
        if not os.path.isdir(output_dir):
            print>>sys.stderr, "No se pudo crear el directorio '"+output_dir+"'"
            print>>sys.stderr, "OSError: ", e
            exit(-2)
    output_dir += '/'
    names = {}

    for f in files:
        try: l = open(f, 'r')
        except IOError: print>>sys.stderr, "No se puede abrir el archivo", f
        else:
            n = 0
            for line in l:
                n += 1
                try:
                    dict_line = json.loads(line)
                except ValueError:
                    print>>sys.stderr, "%s (linea %d): Json corrupto." % (f,n)
                    break
                if dict_line['DESCRIBE'] != 0 or dict_line['ASK'] != 0:
                    continue
                try:
                    query = Query(dict_line['query'])
                except ValueError, e:
                    print>>sys.stderr, "%s (linea %d): %s" % (f,n,str(e))
                    continue
                if not to_ask:
                    try:
                        querys = query.split_optional()
                    except NotImplementedError, e:
                        print>>sys.stderr, "%s (linea %d): %s" % (f,n,str(e))
                        continue
                    except KeyboardInterrupt:
                        exit(-2)
                    except Exception, e:
                        print>>sys.stderr, "%s (linea %d): Error desconocido.\n %s" % (f,n,str(e))
                        continue
                else:
                    query.to_ask()
                    querys = [query ]
                #Write output
                ip = dict_line['ip']
                dir = output_dir + ip + '/'
                if not names.has_key(ip):
                    names[ip] = 1
                    os.makedirs(dir)
                else:
                    names[ip] += 1
                for i, q in enumerate(querys):
                    filename = str(names[ip]).zfill(4)
                    if len(querys) != 1:
                        filename += '.' + str(i)
                    output_name = dir + filename
                    if verbose:
                        print "### " + output_name + ext + " ###"
                        print str(q)
                    if not no_save:
                        with open(output_name + ext, 'w') as out:
                            out.write(str(q))
                    if save_raw and i == 0:
                        if output_name[-2] == '.':
                            output_name = output_name [:-2]
                        with open(output_name + '.raw' + ext,'w') as out:
                            #out.write(str(q.raw))
                            out.write(dict_line['query'])
                del querys
            l.close()
