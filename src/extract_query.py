#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys, json, re, getopt

help_string = """Uso: extract_query [opciones] archivos
Extrae las consultas de un log json y hace cambios en ellas.

Modificacion de consultas:
    --exclude-optional  Excluye los OPTIONAL de las consultas
    --exclude-union     Excluye los UNION de las consultas
    --exclude-graph     Excluye los GRAPH de las consultas
    --split-optional    Divide cada OPTIONAL en 2 consultas.
    --construct         Reemplaza la consulta con un CONSTRUCT vacio
    --construct-copy    Reemplaza la consulta con un CONSTRUCT con los mismos
                        argumentos que el WHERE

Otras opciones:
    -o, --output        Cambia la carpeta de salida predeterminada
    -h, --help          Muestra esta ayuda y termina"""

re_prefix = re.compile(r'PREFIX (.*?): <(.*?)>', re.IGNORECASE)

def find_par(alist, start): #if alist[start] == '{'
    c = 0
    for i in range(start+1, len(alist)):
        key = alist[i]
        if key == '{': c += 1
        elif key == '}':
            if c == 0: return i
            else: c -= 1
    return -1

class Query:
    def __init__(self, raw_str):
        self.raw = raw_str
        string = raw_str.replace('{',' { ').replace('}',' } ')
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
        self.query_type = string[x:i].strip()
        #
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
        #print items
        alist = []
        start = items.index('{')
        end   = find_par(items, start)
        i = start + 1
        c = 0
        while i < end:
            if items[i] == '.' and c == 3:
                alist.append( (items[i-3], items[i-2], items[i-1]) )
                c = 0
            elif items[i] == '{':
                alist.append( self.format( items[i:end]) )
                i = find_par(items, i)
            elif items[i] in ['OPTIONAL', 'UNION'] and items[i+1] == '{':
                alist.append( (items[i], self.format(items[i:end])) )
                i = find_par(items, i+1)
            elif items[i] == 'GRAPH' and items[i+2] == '{':
                alist.append( (items[i], items[i+1], self.format(items[i+1:end])) )
                i = find_par(items, i+2)
            else:
                c +=1
            i += 1
        return alist

    def str_prefix(self):
        string = ""
        for key in self.prefix:
            string += 'PREFIX ' + key + ': <' + self.prefix[key] + '>\n'
        return string

    def str_where(self):
        return 'WHERE {\n' + self.str_deep(self.where, 1, op=False) + '}\n'    #TODO

    def str_deep(self, alist, deep=0, un=True, op=True, gr=True ):
        string = ''
        for t in alist:
            if type(t) == type([]):
                string += '\t'*deep + '{\n' + self.str_deep(t, deep + 1, un,op,gr) + '\t'*deep + '}\n'
            elif type(t) == type(()):
                if t[0] == 'OPTIONAL' and op:
                    string += '\t'*deep + 'OPTIONAL {\n' + self.str_deep(t[1], deep + 1, un,op,gr) + '\t'*deep + '}\n'
                elif t[0] == 'UNION' and un:
                    string += '\t'*deep + 'UNION {\n' + self.str_deep(t[1], deep + 1, un,op,gr) + '\t'*deep + '}\n'
                elif t[0] == 'GRAPH' and gr:
                    string += '\t'*deep + ' '.join(t[:2]) + ' {\n' + self.str_deep(t[2], deep + 1, un,op,gr) + '\t'*deep + '}\n'
                elif len(t) == 3 and type(t[2]) != type([]):
                    string += '\t'*deep + ' '.join(t) + ' .\n'
                else: print >> sys.stderr, t, 'no procesado.'
            else: print >> sys.stderr, t, 'no procesado.'
        return string

    def __str__(self):
        return self.str_prefix() + self.query_type + '\n' + self.str_where() +  self.mods

if __name__ == '__main__':
    exclude_optional = False
    exclude_union = False
    exclude_graph = False
    split_optional = False
    construct = False
    construct_copy = False
    output = "results"
    
    try: options, files = getopt.gnu_getopt(sys.argv[1:], 'o:h',
            ["exclude-optional", "exclude-union", "exclude-graph",
             "split-optional", "construct", "construct-copy", "output=",
             "help"])
    except Exception,e:
        print str(e)
        exit(-1)

    set_opt = set([opt for opt, arg in options])
    if len(set_opt & set(("--exclude-optional","--split-optional"))) > 1:
        print>>sys.stderr, "exclude-optional y split-optional son incompatibles"
        exit(-1)
    if len(set_opt & set(("--construct","--construct-copy"))) > 1:
        print>>sys.stderr, "construct y construct-copy son incompatibles"
        exit(-1)

    for opt, arg in options:
        if opt in ("--help", "-h"):       print help_string; exit(0)
        elif opt in ("--output", "-o"):   output           = arg
        elif opt == "--exclude-optional": exclude_optional = True
        elif opt == "--exclude-union":    exclude_union    = True
        elif opt == "--exclude-graph" :   exclude_graph    = True
        elif opt == "--split-optional":   split_optional   = True
        elif opt == "--construct":        construct        = True
        elif opt == "--construct-copy":   construct_copy   = True

    for f in files:
        try: l = open(f, 'r')
        except IOError: print>>sys.stderr, "No se puede abrir el archivo", f
        else:
            with l: content = l.read().strip()
            for line in content.split('\n'):
                dict_line = json.loads(line)
                query = Query(dict_line['query'])
                #query.query_type = 'CONSTRUCT'
                print query
                print '#'*120
