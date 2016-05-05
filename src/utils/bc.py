#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys, time
import networkx as nx
import pickle

def calBC(G, normalized=False, directional=True):
    BC    = {}
    nodes = G.nodes()
    for s in nodes: #paralelo
        BC[s] = 0.0
    for s in nodes:
        P     = {}
        sigma = {}
        d     = {}
        S     = {}
        # Inicialización
        for t in nodes: #paralelo
            P[t] = []
            sigma[t] = 0.0
            d[t] = -1
        sigma[s] = 1.0
        d[s] = 0
        phase = 0
        S[phase] = [s]
        count = 1
        # Shorted Path
        while count > 0:
            count = 0
            for v in S[phase]:
                for w in G.neighbors(v):
                    if d[w] < 0:
                        if not S.has_key(phase+1):
                            S[phase+1] = []
                        S[phase+1].append(w)
                        count += 1
                        d[w] = d[v] + 1
                    if d[w] == d[v] + 1:
                        sigma[w] += sigma[v]
                        P[w].append(v)
            phase += 1
        phase -= 1
        # Dependency accum
        delta = {}
        for t in nodes:
            delta[t] = 0.0
        while phase > 0:
            for w in S[phase]:
                for v in P[w]:
                    delta[v] += (sigma[v]/sigma[w])*(1+delta[w]) #error
                BC[w] += delta[w]
            phase -= 1
    if normalized:
        l = float(len(nodes))
        if directional:
            fn = 1/((l-2)*(l-1))
        else:
            fn = 2/((l-2)*(l-1))
        for key in BC:
            BC[key] = BC[key] * fn
    return BC

if __name__ == '__main__':
    filename = sys.argv[1]
    with open(filename, 'rb') as f:
        G = pickle.load(f)
    start = time.time()
    BC1 = calBC(G, normalized=True, directional=True)
    print(BC1.values()[:10])
    print("\tTime: %.4F" % (time.time()-start))

    start = time.time()
    BC2 = nx.betweenness_centrality(G)
    print(BC2.values()[:10])
    print("\tTime: %.4F" % (time.time()-start))
