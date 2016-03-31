#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys, copy

replaces = [('{',' { '), ('}',' } '), ('[',' [ '), (']',' ] '),
            (';',' ; '), (',',' , ')]
url_repl = [('(',' ( '), (')', ' ) '), ('.',' . ')]
lit_repl = [('<',' <'), ('>','> '), ('"',' "'), ('"','" ')]
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
        for a, b in lit_repl:
            raw_str = raw_str.replace(a,b)
        self.raw = ''
        for s in raw_str.split():
            if s[0] != '<' and s[0] != '"':
                for a,b in url_repl:
                    s = s.replace(a,b)
            self.raw += s + ' '
        for a, b in replaces:
            self.raw = self.raw.replace(a,b)
        self.raw = ' '.join(self.raw.split())
        self.lower = self.raw.lower()
        #Check query type
        first_brack = self.lower.find('{')
        head = self.lower[:first_brack]
        if 'select ' in head:
            self.head  = self.raw[:head.find('select')]
        elif 'construct ' in head:
            self.head  = self.raw[:head.find('construct')]
#            first_brack += self.lower[first_brack+1:].find('{') +  1
            first_brack  = self.lower.find('where')
            first_brack += self.lower[first_brack:].find('{')
        else:
            raise ValueError('Tipo de consulta no soportada.')
        last_brack = find_par(self.lower, first_brack)
        self.qarg  = self.raw[len(self.head):first_brack]
        self.where = self.raw[first_brack:last_brack+1]
        self.tail  = self.raw[1+last_brack:]
#        print 'head:', self.head
#        print 'qarg:', self.qarg
#        print 'wher:', self.where
#        print 'tail:', self.tail
        if self.qarg == '' or self.where == '':
            raise ValueError('Consulta vacia.')
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
                    option += [tr]
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
                    # TODO: fixme filter () . <- the dot
                    if litems[i+1] == '(':
                        i = find_par(litems, i+1, ('(',')'))
                    elif litems[i+2] == '(':
                        i = find_par(litems, i+2, ('(',')'))
                    try:
                        if litems[i+1] == '.': i += 1
                    except IndexError:
                        pass
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
                    #TODO
                    raise NotImplementedError('Parentesis cuadrados aun no implementados.')
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
                raise RuntimeError("Pila no vacia: %r" % str(stack))
            return triple, option

        return rec_search(litems[1:-1], items[1:-1])

    def to_construct(self):
        self.qarg = "CONSTRUCT WHERE"

    def split_optional(self):
        triples, optionals = self.get_triples()
        base = ''
        for t in triples:
            base += ' '.join(t) + ' . '
        self.qarg = 'CONSTRUCT { ' + base
        self.where = '} WHERE ' + self.where
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

    def __str__(self):
        return self.head + self.qarg + self.where + self.tail

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
#                t, o = q.get_triples()
                querys = q.split_optional()
            except ValueError, e:
                print f, e
            for qq in querys:
                print str(qq), '\n'
#            print 'TRIPLES:'
#            for i in t: print '\t',i
#            print 'OPTIONALS:'
#            for i in o: print '\t',i
#            print ''
