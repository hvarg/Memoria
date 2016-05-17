#include <stdlib.h>
#include "structures.h"
#include "centrality.h"

float *betweenness_centrality(struct graph *G)
{
  return betweenness_centrality_range(G, 0, G->size);
}

float *betweenness_centrality_range(struct graph *G, int init, int end)
{
  float *BC = (float *) malloc(sizeof(float) * G->size);
  int s, t, v, w, ph, count, *tmp,
      *d = (int *) malloc(sizeof(int) * G->size);
  float *sigma = (float *) malloc(sizeof(float) * G->size),
        *delta = (float *) malloc(sizeof(float) * G->size);
  struct list **P = (struct list **) malloc(sizeof(struct list*) * G->size),
              **S = (struct list **) malloc(sizeof(struct list*) * G->size);
  // is better if S is small, like a dinamic array or something.
  struct item *elem1, *elem2;
  for (s=0; s < G->size; s++){
    BC[s] = 0.0;
    S[s] = NULL;
    P[s] = NULL;
  }
  if (end > G->size) end = G->size;
  for (s=init; s < end; s++) {
    // free S (at least)
    for (t=0; t < G->size; t++) {
      P[t] = new_list();
      sigma[t] = 0.0;
      d[t] = -1;
    }
    sigma[s] = 1.0;
    d[s] = 0;
    ph = 0;
    S[ph] = new_list();
    tmp = (int*) malloc(sizeof(int));
    *tmp = s;
    list_add(S[ph], tmp);
    count = 1;
    while (count > 0){
      count = 0;
      for (elem1 = S[ph]->first; elem1 != NULL; elem1 = elem1->next) {
        v = *((int *) elem1->value);
        for (elem2 = G->nodes[v]->neighbors->first;
             elem2 != NULL; elem2 = elem2->next) {
          w = *((int *) elem2->value);
          if (d[w] < 0) {
            if (S[ph+1] == NULL) S[ph+1] = new_list();
            tmp = (int*) malloc(sizeof(int));
            *tmp = w;
            list_add(S[ph+1], tmp);
            count++;
            d[w] = d[v] + 1;
          }
          if (d[w] == d[v] + 1) {
            sigma[w] += sigma[v];
            tmp = (int*) malloc(sizeof(int));
            *tmp = v;
            list_add(P[w], tmp);
          }
        }
      }
      ph++;
    }
    ph--;
    for (t=0; t < G->size; t++)
      delta[t] = 0.0;
    while (ph > 0) {
      for (elem1 = S[ph]->first; elem1 != NULL; elem1 = elem1->next) {
        w = *((int *) elem1->value);
        for (elem2 = P[w]->first; elem2 != NULL; elem2 = elem2->next) {
          v = *((int *) elem2->value);
          delta[v] += (sigma[v]/sigma[w]) * (1+delta[w]);
        }
        BC[w] += delta[w];
      }
      ph--;
    }
    for (t=0; t < G->size; t++) {
      if (S[t] != NULL){
        list_del(S[t]);
        S[t] = NULL;
      }
      if (P[t] != NULL) {
        list_del(P[t]);
        P[t] = NULL;
      }
    }
  }
  free(d);
  free(sigma);
  free(delta);
  free(P);
  free(S);
  return BC;
}

/* vim: set ts=2 sw=2 sts=2 tw=80 : */
