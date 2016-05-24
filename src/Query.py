#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys, copy, re

# This regex is better but slow
_regex  = r'(?P<all>'				# group to 'all'
_regex += r'<[^<>"{}|^`]*?>|'			# uri or
_regex += r'(""").*?(""")|' 			# double quoted long string or
_regex += r"(''').*?(''')|"			# single quoted long string or
_regex += r'"[^"\\]*(?:\\.[^"\\]*)*"|'		# double quoted string or
_regex += r"'[^'\\]*(?:\\.[^'\\]*)*'"		# single quoted string
_regex += r')'

#regex = re.compile(r'(<[^\s]*?>|"{1,3}.*?"{1,3})|\'{1,3}.*?\'{1,3}')
regex = re.compile(_regex)
rdot  = re.compile(r'([^\s]*?)\.([ \?\}\{]|filter|optional)', re.IGNORECASE)

replaces = [('{',' { '), ('}',' } '), ('[',' [ '), (']',' ] '),
            (';',' ; '), (',',' , '), ('(',' ( '), (')',' ) '),
            ('/',' / '), ('?',' ?'), (' @','@'), (' ^^ ','^^'), (' ^^','^^')]
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

################################# Query Class #################################
class Query:
    def __init__(self, raw_str):
        # Normaliza la query y reemplaza los string y uris inmutables.
        #immut = regex.findall(raw_str)
	immut = [_.groupdict()['all'] for _ in regex.finditer(raw_str)]
        self.raw = regex.sub(' %s ', raw_str)
        self.raw = rdot.sub(r'\1 . \2', self.raw)
        for a,b in replaces:
            self.raw = self.raw.replace(a,b)
        self.raw = '\t'.join(self.raw.split())
        self.lower = self.raw.lower()

        # Verifica el tipo de consulta y la separa en sus partes.
        construct = True
        i = self.lower.find('construct')
        if i < 0:
            construct = False
            i = self.lower.find('select')
        if i < 0:
            raise ValueError('Tipo de consulta no soportada.')
        self.head = self.raw[:i]
        try:
            j = self.lower[i:].find('{') + i
            k = find_par(self.lower, j)  + 1
            n = self.lower[k:].find('{')
            if n > 0 and construct:
                j, k = n+k, find_par(self.lower, n+k)
        except:
            raise ValueError('Consulta corrupta.')
        self.qarg  = self.raw[i:j]
        self.where = self.raw[j:k]
        self.tail  = self.raw[k:]
        ssum = self.head +'\0'+ self.qarg +'\0'+ self.where +'\0'+ self.tail
        try:
            ssum = ssum % tuple(immut)
        except:
            raise ValueError('Consulta corrupta.')
        self.raw = ssum #no se usa
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
            self.rpl.append( ('\t/\t', ' '+var_name+' . '+var_name+' ') )
        elif orig == '[\t]':
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
                if t == '#':
                    i = l
                elif t == '{':
                    if len(stack) == 3:
                        triple.append( tuple(stack) )
                        stack = []
                    j = find_par(litems, i)
                    tr, op  = rec_search(litems[i+1:j], items[i+1:j])
                    triple += tr
                    option += op
                    i = j
                elif t == '(':
                    # ( uri ) *
                    if i+3 < l and litems[i+2] == ')' and litems[i+3] == '*':
                        stack.append( '('+items[i+1]+')*' )
                        i+=3
                elif t == 'select':
                    while i+1 < l and litems[i+1] != '{':
                        i += 1
                elif t == 'optional'and litems[i+1] == '{':
                    j = find_par(litems, i+1)
                    tr, op  = rec_search(litems[i+2:j], items[i+2:j])
                    option += [tr]
                    i = j
                    if i-1 > 0 and  litems[i-1] != '.':
                        if len(stack) == 3:
                            triple.append( tuple(stack) )
                            stack = []
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
                    # Ignora los service
                    i = find_par(litems, i+2)
                elif t == 'order' and litems[i+1] == 'by':
                    i += 2
                    while i <  l and litems[i][0] == '?':
                        i += 1
                    i -= 1
                elif t in ['limit', 'offset']:
                    i += 1
                elif t == 'asc' and litems[i+1] == '(':
                    i = find_par(litems, i+1, ('(',')'))
                elif t == 'values':
                    if litems[i+2] == '{':
                        i = find_par(litems, i+2)
                    else:
                        if litems[i+1] == '(':
                            i = find_par(litems, i+1, ('(',')'))
                        if litems[i+1] == '{':
                            i = find_par(litems, i+1)
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
                    # Next dot
                    if i+1 < l and litems[i+1] == '.':
                        if len(stack) == 3:
                            triple.append( tuple(stack) )
                            stack = []
                        i += 1
                    # Prev dot
                    if i-1 > 0 and  litems[i-1] != '.':
                        if len(stack) == 3:
                            triple.append( tuple(stack) )
                            stack = []
                elif t == ';':
                    a, b = stack.pop(), stack.pop()
                    if i+1 == l or litems[i+1] in ['optional','.','filter','service']:
                        c = stack.pop()
                    else:
                        c = stack[-1]
                    triple.append( (c, b, a) )
                elif t == ',':
                    a = stack.pop()
                    if i != l-1:
                        b, c = stack[-2], stack[-1]
                    else:
                        b, c = stack.pop(), stack.pop()
                    triple.append( (c, b, a) )
                elif t == '.':
                    if len(stack) > 1 and stack[-1] != '.':
                        triple.append( tuple(stack) )
                        stack = []
                elif t == '/':
                    var_name = self.to_var('/')
                    if len(stack) != 2:
                        raise IndexError('No hay 2 elementos en la pila.')
                    stack.append(var_name)
                    triple.append( tuple(stack) )
                    stack = [var_name,]
                elif t == '[':
                    j = find_par(litems,i,('[',']'))
                    if j == i+1:
                        var_name = self.to_var('[\t]')
                        stack.append( var_name )
                    else:
                        var_name = self.to_var('[')
                        if len(stack) == 0:
                            if l > j+1 and litems[j+1] not in ['filter', 'optional']:
                                stack.append( var_name )
                            self.rpl.append( ('[', var_name) )
                            if litems[j-1] == ';':
                                self.rpl.append( (';\t]', '.') )
                            else:
                                self.rpl.append( (']', '') )
                        else:
                            stack.append( var_name )
                            self.rpl.append( ('[', var_name +' . ' +var_name) )
                            if l > j+1 and litems[j+1] not in ['.',';',',',']']:
                                self.rpl.append( (']', '.') )
                            else:
                                self.rpl.append( (']', '') )
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
            tmp.qarg += string + '} WHERE '
            alist.append( tmp )
        self.qarg += '} WHERE '
        return alist

    def check_construct(self):
        i = self.qarg.find('{')
        if i < 0: return False
        try:
            j = find_par(self.qarg, i)
        except:
            return False
        for e in self.qarg[i+1:j].split():
            if e[0] != '?' and e[0] != '.':
                return True
        return False

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
