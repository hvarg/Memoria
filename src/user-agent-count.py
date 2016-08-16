#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Example:
#114.94.18.47<sep>20/Aug/2014:09:03:04 -0400<sep>PREFIX void: <http://rdfs.org/ns/void#>  PREFIX dv: <http://bio2rdf.org/bio2rdf.dataset_vocabulary:>  SELECT ?type (str(?count) AS ?count)  WHERE {   ?x void:subset [    a dv:Dataset-Type-Count;    void:class ?type;    void:entities ?count  ]}   ORDER BY DESC(?count) <sep>cu.linkedspl.bio2rdf.org<sep>Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.143 Safari/537.36<sep>200<sep>643

import sys, os

if __name__ == '__main__':
    dic = {}
    file_list = sys.argv[1:]
    # Recursivo
    for f in file_list:
        if os.path.isdir(f):
            file_list.remove(f)
            for new_file in os.listdir(f):
                file_list.append(f + '/' + new_file)

    for name in file_list:
        with open(name) as f:
            nline = 0
            for line in f:
                nline += 1
                sp = line.split('<sep>')
                try:
                    user_agent = sp[4]
                    if dic.has_key(user_agent):
                        dic[user_agent] += 1
                    else:
                        dic[user_agent] = 1
                except:
                    print>>sys.stderr, name +'('+str(nline)+')', sp[-1][:-1]
                    lfile = name
    for key in dic:
        print dic[key], '\t', key
