#ifndef CENTRALITY_H_
#define CENTRALITY_H_

float *betweenness_centrality(struct graph *G);
float *betweenness_centrality_range(struct graph *G, int init, int end);

#endif
/* vim: set ts=2 sw=2 sts=2 tw=80 : */
