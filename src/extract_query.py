import sys, json, re

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
    with open(sys.argv[1], 'r') as q:
        content = q.read().strip()
    #
    for line in content.split('\n'):
        dict_line = json.loads(line)
        query = Query(dict_line['query'])
        #query.query_type = 'CONSTRUCT'
        print query
        print '#'*120
