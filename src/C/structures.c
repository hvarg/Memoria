#include "structures.h"
#include <stdlib.h>

/* Create a new list. */
struct list *new_list()
{
  struct list * new = (struct list *) malloc(sizeof(struct list));
  new->first = NULL;
  new->last  = NULL;
  new->size  = 0;
  return new;
}

/* Add a element to a list. The element is stored in a 'item'. */
void list_add(struct list *alist, void *element)
{
  struct item *new = (struct item *) malloc(sizeof(struct item));
  new->value = element;
  new->next  = NULL;
  if (alist->first == NULL) {
    alist->first = new;
    alist->last  = new;
  } else {
    (*alist->last).next = new;
    alist->last = new;
  }
  alist->size++;
}

/* Delete a list (and free). */
void list_del(struct list *alist)
{
  struct item *act, *next;
  for(act = alist->first; act != NULL; act = next){
    next = act->next;
    free(act->value);
    free(act);
  }
  free(alist);
}

/* Create a new graph with 'size' nodes. */
struct graph *new_graph(unsigned int size)
{
  struct graph *new = (struct graph *) malloc(sizeof(struct graph));
  new->nodes = (struct node **) malloc(sizeof(struct node *) * size);
  new->size  = size;
  return new;
}

/* Create a new node. */
struct node *new_node(unsigned int id, struct list * neig)
{
  struct node *new = (struct node *) malloc(sizeof(struct node));
  new->id = id;
  new->neighbors = neig;
  return new;
}

/* Add the node N to graph G. */
void graph_add_node(struct graph *G, struct node *N)
{
  G->nodes[N->id] = N;
}

/* Delete the node N. */
void node_del(struct node *N)
{
  list_del(N->neighbors);
  free(N);
}

/* Delete the graph G. */
void graph_del(struct graph *G)
{
  int i;
  for(i=0; i<G->size; node_del(G->nodes[i++]));
  free(G->nodes);
  free(G);
}

/* vim: set ts=2 sw=2 sts=2 tw=80 : */
