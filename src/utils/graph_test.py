import sys
import networkx as nx

if __name__ == "__main__":
    N = int(sys.argv[1])
    print N
    G_ba = nx.barabasi_albert_graph(N, 3)
    G_er = nx.gnp_random_graph(N, 0.01)
    G_ws = nx.connected_watts_strogatz_graph(N, 4, 0.1)
    O_ba = open('ba_'+str(N)+'.sg', 'w')
    O_er = open('er_'+str(N)+'.sg', 'w')
    O_ws = open('ws_'+str(N)+'.sg', 'w')
    for G, O in [(G_ba, O_ba), (G_er, O_er), (G_ws, O_ws)]:
        for i in range(0,N):
            print>>O, str(i)+':',
            for j in nx.neighbors(G,i):
                print>>O, j,
            print>>O
    O_ba.close()
    O_er.close() 
    O_ws.close() 
