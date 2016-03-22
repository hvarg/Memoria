#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys, os, getopt
import json, re, copy

help_string = """Uso: extract_query [opciones] archivos
Extrae las consultas de un log json y hace cambios para retornar los triples
consultados. Por defecto ignora los OPTIONAL.

Modificacion de consultas:
    --split-optional    Crea una consulta adicional por cada OPTIONAL.

Otras opciones:
    --no-save           No guarda las consultas.
    --save-raw          Tambien guarda las consultas originales.
    --extension <file>  Especifica la extension (por defecto '.sparql').
    -V, --verbose       Muestra por salida estandar las consultas resultantes.
    -o, --output <file> Cambia la carpeta de salida predeterminada.
    -h, --help          Muestra esta ayuda y termina."""

re_prefix = re.compile(r'PREFIX (.*?): <(.*?)>', re.IGNORECASE)

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
        self.raw = raw_str
        #DEBUG:
        if "BASE" in raw_str or "DESCRIBE" in raw_str or "ASK" in raw_str:
            print>>sys.stderr, "SE ENCONTRO UN BASE, ASK O DESCRIBE"
        string = raw_str.replace('{',' { ').replace('}',' } ')
        string = string.replace('(',' ( ').replace(')',' ) ')
        string = ' '.join(string.split())
        #
        prefix = re_prefix.findall(string)
        self.prefix = {}
        for key, value in prefix:
            self.prefix[key] = value
        #TODO ignore case
        last = prefix[-1][1]
        x = string.find(last) + len(last) + 1
        i = string.find('WHERE')
        self.raw_type = string[x:i].strip()
        fs = self.raw_type.find(' ')
        self.qtype = self.raw_type[:fs]
        if self.qtype == "SELECT":
            self.qarg = [self.raw_type[fs+1:]]
        elif self.qtype == "CONSTRUCT":
            self.qarg = self.format(self.raw_type[fs+1:].split())
        else:
            print>>sys.stderr, "Tipo de query no soportado:", self.qtype
            raise ValueError
        a, count  = 0, 0
        while i < len(string): 
            if string[i] == '{':
                if a == 0: a = i
                count += 1
            elif string[i] == '}':
                if count == 1: break
                count -= 1
            i += 1
        self.raw_where = string[a:i+1]
        self.mods  = string[i+1:].strip()
        self.where = self.format(self.raw_where.split())

    def format(self, items):
        #https://www.w3.org/TR/rdf-sparql-query/#sparqlGrammar
        alist = []
        start = items.index('{')
        end   = find_par(items, start)
        i = start + 1
        c = 0
        while i < end:      #TODO add FILTER and ';'
            if items[i] == '.' and c == 3:  #TODO fixme: c>3
                alist.append( (items[i-3], items[i-2], items[i-1]) )
                c = 0
            elif items[i] == '{':
                alist.append( self.format( items[i:end]) )
                i = find_par(items, i)
            elif items[i] in ['OPTIONAL', 'UNION'] and items[i+1] == '{':
                alist.append( (items[i], self.format(items[i:end])) )
                i = find_par(items, i+1)
            elif items[i] == 'GRAPH' and items[i+2] == '{':
                alist.append((items[i],items[i+1],self.format(items[i+1:end])))
                i = find_par(items, i+2)
            elif items[i] == 'FILTER' and items[i+1] == '(':
                j = find_par(items, i+1, ('(', ')') )
                alist.append( (' '.join(items[i:j+1]), ) )
                i = j
            else:
                c += 1
            i += 1
        return alist

    def triples(self, target_list=None):
        if target_list == None: target_list = self.where
        def rec_tr(alist):
            new_list = []
            for item in alist:
                if item[0] in ["UNION", "GRAPH"]:
                    item = item[-1]
                elif len(item) == 3:
                    #if not (item[0][0] == item[1][0] == item[2][0] == "?"):
                    new_list.append( item )
                if type(item) == list:
                    tmp = rec_tr(item)
                    new_list += tmp
            return new_list
        return rec_tr( target_list )

    def to_construct(self):
        self.qtype = "CONSTRUCT"
        self.qarg  = self.triples()
        return [ self ]

    def split_optional(self):
        def rec_op(alist):
            new_list = []
            for item in alist:
                if item[0] == 'OPTIONAL':
                    new_list.append(self.triples(item[1]))
                elif item[0] in ["UNION", "GRAPH"]:
                    item = item[-1]
                if type(item) == list:
                    new_list += rec_op( item )
            return new_list
        self.to_construct()
        triples = self.triples()
        opts = rec_op(self.where)
        new_querys = [self, ]
        for ltr in opts:
            new_querys.append( copy.copy(self) )
            new_querys[-1].qarg = triples + ltr
        return new_querys

    def str_prefix(self):
        string = ""
        for key in self.prefix:
            string += 'PREFIX ' + key + ': <' + self.prefix[key] + '>\n'
        return string

    def str_where(self):
        return 'WHERE {\n' + self.str_deep(self.where, 1) + '}\n'

    def str_qtype(self):
        if self.qtype == "CONSTRUCT":
           return self.qtype + ' {\n' + self.str_deep(self.qarg, 1) + '}\n'
        else:
           return self.qtype + ' ' + self.qarg[0] + '\n'

    def str_deep(self, alist, deep=0):
        string = ''
        for t in alist:
            if type(t) == list:
                string += '\t'*deep + '{\n' + \
                          self.str_deep(t, deep + 1) + '\t'*deep + '}\n'
            elif type(t) == tuple:
                if t[0] in ["OPTIONAL", "UNION"]:
                    string += '\t'*deep + t[0] + ' {\n' + \
                              self.str_deep(t[1], deep + 1) + '\t'*deep + '}\n'
                elif t[0] == 'GRAPH':
                    string += '\t'*deep + ' '.join(t[:2]) + ' {\n' + \
                              self.str_deep(t[2], deep + 1) + '\t'*deep + '}\n'
                elif len(t) == 1:
                    string += '\t'*deep + t[0] + '\n'
                elif len(t) == 3 and type(t[-1]) != list:
                    string += '\t'*deep + ' '.join(t) + ' .\n'
                else:
                    print>>sys.stderr, t, 'no procesado.'
            else:
                string += '\t'*deep + str(t)
                print>>sys.stderr, t, 'no formateado.'
        return string

    def __str__(self):
        return self.str_prefix() + self.str_qtype() + \
               self.str_where() +  self.mods
###############################################################################

################################ Main Function ################################
if __name__ == '__main__':
    split_optional   = False
    verbose          = False
    save_raw         = False
    no_save          = False
    output_dir       = "results"
    ext              = ".sparql"

    try: options, files = getopt.gnu_getopt(sys.argv[1:], 'o:hV',
            ["split-optional", "output=", "help", "verbose", "save-raw",
             "extension=", "no-save"])
    except Exception,e:
        print str(e)
        exit(-1)

    for opt, arg in options:
        if opt in ("--help", "-h"):       print help_string; exit(0)
        elif opt in ("--output", "-o"):   output_dir       = arg
        elif opt in ("--verbose", "-V"):  verbose          = True
        elif opt == "--split-optional":   split_optional   = True
        elif opt == "--save-raw":         save_raw         = True
        elif opt == "--no-save":          no_save          = True
        elif opt == "--extension":        ext              = arg

    try: 
        os.makedirs(output_dir)
    except OSError:
        if not os.path.isdir(output_dir):
            print>>sus.stderr, "No se pudo crear el directorio"
    output_dir += '/'
    names = {}

    for f in files:
        try: l = open(f, 'r')
        except IOError: print>>sys.stderr, "No se puede abrir el archivo", f
        else:
            with l: content = l.read().strip()
            for line in content.split('\n'):
                dict_line = json.loads(line)
                query = Query(dict_line['query'])
                #Do things to a query
                if split_optional:
                    querys = query.split_optional()
                else:
                    querys = query.to_construct()
                #Write output
                ip = dict_line['ip']
                if not names.has_key(ip): names[ip] = 1
                else: names[ip] += 1
                for i, q in enumerate(querys):
                    filename = ip + '_' + str(names[ip]).zfill(3)
                    if len(querys) != 1:
                        filename = filename + '.' + str(i)
                    output_name = output_dir + filename
                    if verbose:
                        print "### " +output_name + ext + " ###"
                        print q
                    if not no_save:
                        with open(output_name + ext, 'w') as out:
                            out.write(str(q))
                    if save_raw and i == 0:
                        if output_name[-2] == '.':
                            output_name = output_name [:-2]
                        with open(output_name + '_raw' + ext,'w') as out:
                            out.write(str(q.raw))
