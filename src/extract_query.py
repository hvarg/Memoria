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
    -m, --max <int>     Especifica el tamaño maximo de respuesta.
    -V, --verbose       Muestra por salida estandar las consultas resultantes.
    -o, --output <file> Cambia la carpeta de salida predeterminada.
    -h, --help          Muestra esta ayuda y termina."""

################################ Main Function ################################

if __name__ == '__main__':
    maxim      = 0
    verbose    = False
    save_raw   = False
    no_save    = False
    to_ask     = False
    output_dir = "results"
    ext        = ".sparql"

    try: options, files = getopt.gnu_getopt(sys.argv[1:], 'o:hVm:',
            ["output=", "help", "verbose", "max=", "save-raw",
             "extension=", "no-save", "to-ask"])
    except Exception,e:
        print str(e)
        exit(-1)

    for opt, arg in options:
        if opt in ("--help", "-h"):       print help_string; exit(0)
        elif opt in ("--output", "-o"):   output_dir       = arg
        elif opt in ("--max", "-m"):      maxim            = int(arg)
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
    last_ip = None
    out = None
    over_max = None
    out_raw = None
    log = open('log', 'a')

    for f in files:
        try: l = open(f, 'r')
        except IOError: print>>sys.stderr, "No se puede abrir el archivo", f
        else:
            n = 0
            for line in l:
                n += 1
                try:
                    dict_line = json.loads(line)
                    size = int(dict_line['response_size'])
                except ValueError:
                    print>>sys.stderr, "%s (linea %d): Json corrupto." % (f,n)
                    break
                if dict_line['DESCRIBE'] != 0 or dict_line['ASK'] != 0:
                    print>>log, "%d\tIgnorado\t%s (%02d)\t<- Consulta no soportada." % (size,f,n)
                    continue
                elif dict_line['error']:
                    print>>log, "%d\tError\t%s (%02d)\t<- Consulta marcada como error." % (size,f,n)
                    continue
                try:
                    query = Query(dict_line['query'])
                except ValueError, e:
                    print>>sys.stderr, "%s (linea %d): %s" % (f,n,str(e))
                    print>>log, "%d\tError\t%s (%02d)\t<- Error en tiempo de ejecucion." % (size,f,n)
                    continue
                if not to_ask:
                    try:
                        querys = query.split_optional()
                    except KeyboardInterrupt:
                        exit(-2)
                    except Exception, e:
                        print>>sys.stderr, "%s (linea %d): Error desconocido.\n %s" % (f,n,str(e))
                        print>>log, "%d\tError\t%s (%02d)\t<- Error en tiempo de ejecucion." % (size,f,n)
                        continue
                else:
                    query.to_ask()
                    querys = [ query ]

                #Write output
                ip   = dict_line['ip']
                filename = output_dir+ip+ext


                if ip != last_ip:
                    last_ip = ip
                    if out != None:
                        out.close()
                        if save_raw: out_raw.close()
                    count = 0
                    if os.path.isfile(filename):
                        with open(filename, 'r') as tmp:
                            for _ in tmp:
                                count +=1
                    out = open(filename, 'a')
                    if save_raw: out_raw = open(output_dir+ip+'.raw'+ext, 'a')

                if maxim > 0 and over_max == None:
                    mcount = 0
                    if os.path.isfile(output_dir+'huge_querys'+ext):
                        with open(output_dir+'huge_querys'+ext, 'r') as tmp:
                            for _ in tmp:
                                mcount +=1
                    over_max = open(output_dir+'huge_querys'+ext, 'a')

                for q in querys:
                    if verbose:
                        print str(q)
                    if not no_save:
                        if maxim > 0 and size > maxim:
                            over_max.write(str(q)+'\n')
                            mcount += 1
                            print>>log, "%d\tHecho\t%s (%02d)\t->\t%s (%02d)" % (size,f,n,output_dir+'huge_querys'+ext, mcount)
                        else:
                            out.write(str(q)+'\n')
                            count += 1
                            print>>log, "%d\tHecho\t%s (%02d)\t->\t%s (%02d)" % (size,f,n,filename, count)
                    if save_raw:
                        out_raw.write(dict_line['query']+'\n')
                del querys
            l.close()
    if out != None: out.close()
    if over_max != None: over_max.close()
    if out_raw != None: out_raw.close()
