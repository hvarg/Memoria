#ifndef STRUCTURES_H_
#define STRUCTURES_H_

struct item{
  void *value;
  struct item *next;
};

struct list{
  struct item *first;
  struct item *last;
  unsigned int size;
};

struct node{
  unsigned int id;
  struct list *neighbors;
};

struct graph{
  struct node **nodes;
  unsigned int size;
};

struct list *new_list();
void list_add(struct list *alist, void *element);
void list_del(struct list *alist);

struct graph *new_graph(unsigned int size);
struct node  *new_node(unsigned int id, struct list * neig);
void graph_add_node(struct graph *G, struct node *N);
void node_del(struct node *N);
void graph_del(struct graph *G);

#endif
/* vim: set ts=2 sw=2 sts=2 tw=80 : */
