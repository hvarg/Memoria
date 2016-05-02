#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys, copy, re

#regex = re.compile(r'([<"].*?[">])')
regex = re.compile(r'(<[^\s]*?>|"{1,3}.*?"{1,3})|\'{1,3}.*?\'{1,3}')

replaces = [('{',' { '), ('}',' } '), ('[',' [ '), (']',' ] '),
            (';',' ; '), (',',' , '), ('(',' ( '), (')',' ) '),
            ('.',' . '), (' ^^ ','^^'), (' @','@')]
_letters = "abcdefghijklmnopqrstuvwxyz"

# Encuentra los cierres de parentesis.
def find_par(alist, start, p=('{', '}') ): #if alist[start] == p[0]
    c = 0
    for i in range(start+1, len(alist)):
        key = alist[i]
        if key == p[0]: c += 1
        elif key == p[1]:
            if c == 0: return i
            else: c -= 1
    raise IndexError("No se encontro par.")

############################### The Query Class ###############################
class Query:
    def __init__(self, raw_str):
        # Normaliza la query y reemplaza los string inmutables.
        immut = regex.findall(raw_str)
        self.raw = regex.sub(' %s ', raw_str)
        for a,b in replaces:
            self.raw = self.raw.replace(a,b)
        self.raw = '\t'.join(self.raw.split())
        self.lower = self.raw.lower()

        # Verifica el tipo de consulta y la separa en sus partes.
        first_brack = self.lower.find('{')
        head = self.lower[:first_brack]
        if 'select\t' in head:
            self.head  = self.raw[:head.find('select')]
        elif 'construct\t' in head:
            self.head  = self.raw[:head.find('construct')]
            first_brack  = self.lower.find('where')
            first_brack += self.lower[first_brack:].find('{')
        else:
            raise ValueError('Tipo de consulta no soportada.')
        last_brack = find_par(self.lower, first_brack)

        self.qarg  = self.raw[len(self.head):first_brack]
        self.where = self.raw[first_brack:last_brack+1]
        self.tail  = self.raw[2+last_brack:]
        if self.qarg == '' or self.where == '':
            raise ValueError('Consulta vacia.')
        ssum = self.head +'\0'+ self.qarg +'\0'+ self.where +'\0'+ self.tail
        try:
            ssum = ssum % tuple(immut)
        except:
            raise ValueError('Consulta corrupta.')
        self.raw = ssum
        self.head, self.qarg, self.where, self.tail = ssum.split('\0')
        self.letter_index = 0
        self.rpl = []

    # Asigna una variable auxiliar a una variable muda ([,/) y la guarda en
    # memoria para su posterior conversion.
    # retorna la variable auxiliar.
    def to_var(self, orig):
        var_name = '?_' + _letters[self.letter_index % 26]
        self.letter_index += 1
        if orig == '/':
            self.rpl.append( (' / ', ' '+var_name+' . '+var_name+' ') )
        elif orig == '[':
            self.rpl.append( (orig, var_name) )
        return var_name

    # Obtiene los triples que conformaran el construct.
    def get_triples(self):
        triple = []
        option = []
        litems = self.where.lower().split('\t')
        items  = self.where.split('\t')

        def rec_search(litems, items, stack=None):
            triple = []
            option = []
            if stack == None: stack = []
            i = 0
            l = len(litems)
            while i < l:
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
                    option += [tr]
                    i = j
                elif t == 'union' and litems[i+1] == '{':
                    j = find_par(litems, i+1)
                    tr, op  = rec_search(litems[i+2:j], items[i+2:j])
                    triple += tr
                    option += op
                    i = j
                elif t == 'graph' and litems[i+2] == '{':
                    j = find_par(litems, i+2)
                    tr, op  = rec_search(litems[i+3:j], items[i+3:j])
                    triple += tr
                    option += op
                    i = j
                elif t == 'service' and litems[i+2] == '{':
                    # TODO: not ignore services
                    i = find_par(litems, i+2)
                elif t == 'values':
                    if litems[i+2] == '{':
                        i = find_par(litems, i+2)
                elif t in ['minus', 'exists']:
                    if litems[i+1] == '{':
                        i = find_par(litems, i+1)
                elif t == 'not': pass
                elif t == 'bind':
                    if i+1 < l and litems[i+1] == '(':
                        i = find_par(litems, i+1, ('(',')'))
                elif t == 'filter':
                    if i+1 < l and litems[i+1] == '(':
                        i = find_par(litems, i+1, ('(',')'))
                    elif i+2 < l and litems[i+2] == '(':
                        i = find_par(litems, i+2, ('(',')'))
                    if i+1 < l and litems[i+1] == '.':
                        if len(stack) == 3:
                            triple.append( tuple(stack) )
                            stack = []
                        i += 1
                elif t == ';':
                    a, b = stack.pop(), stack.pop()
                    if i != l-1:
                        c = stack[-1]
                    else:
                        c = stack.pop()
                    triple.append( (c, b, a) )
                elif t == ',':
                    a = stack.pop()
                    if i != l-1:
                        b, c = stack[-2], stack[-1]
                    else:
                        b, c = stack.pop(), stack.pop()
                    triple.append( (c, b, a) )
                elif t == '.':
                    triple.append( tuple(stack) )
                    stack = []
                elif t == '/':
                    var_name = self.to_var('/')
                    if len(stack) != 2:
                        raise IndexError('No hay 2 elementos en el stack.')
                    stack.append(var_name)
                    triple.append( tuple(stack) )
                    stack = [var_name,]
                elif t == '[':
                    #TODO
                    raise NotImplementedError('Parentesis cuadrados aun no implementados.')
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
                raise RuntimeError("Pila no vacia: %r" % str(stack))
            return triple, option

        return rec_search(litems[1:-1], items[1:-1])

    # Transforma la consulta a un CONSTRUCT vacio.
    def to_construct(self):
        self.qarg = "CONSTRUCT WHERE"

    # Transforma la consulta a un ASK vacio.
    def to_ask(self):
        self.qarg = "ASK WHERE"

    # Genera una nueva consulta por cada triple opcional.
    def split_optional(self):
        triples, optionals = self.get_triples()
        base = ''
        for t in triples:
            base += ' '.join(t) + ' . '
        self.qarg = 'CONSTRUCT { ' + base
        self.where = '} WHERE ' + self.where
        # TODO: que pasa si ambas estan vacias?
        if len(triples) > 0:
            alist = [self]
        else:
            alist = []
        for opts in optionals:
            string = ''
            for o in opts:
                string += ' '.join(o) + ' . '
            tmp = copy.copy(self)
            tmp.qarg += string
            alist.append( tmp )
        return alist

    # Transforma la query en un string
    def __str__(self):
        if len(self.rpl) != 0:
            for a,b in self.rpl:
                self.where = self.where.replace(a,b,1)
        q = self.head + self.qarg + self.where + self.tail
        return q.replace('\t',' ')

###############################################################################

################################ Main Function ################################
import json

if __name__ == '__main__':
    files = sys.argv[1:]
    for f in files:
        try: l = open(f, 'r')
        except IOError: print>>sys.stderr, "No se puede abrir el archivo", f
        else:
#            print f
            i = 0
            for line in l:
                raw_query = json.loads(line)['query']
#                print "%s %d\n%s\n" % (f, i, raw_query)
                querys = []
                try:
                    q = Query(raw_query)
                    querys = q.split_optional()
                except ValueError:
                    pass
                except NotImplementedError:
                    pass
                except Exception, e:
                    print "%s (linea %d): %s\n\t%s" % (f, i, e, raw_query)
             #       exit(-1)
                    break
#                    print "%s (linea %d): %s" % (f, i, e)
#                for qq in querys:
#                    print str(qq), '\n'
                i += 1
            l.close()
