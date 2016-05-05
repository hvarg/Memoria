#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define BUFFER_LEN 16

/*******************************  List things.  *******************************/
struct item{
  void *value;
  struct item *next;
};

struct list{
  struct item *first;
  struct item *last;
  unsigned int size;
};

struct list *new_list()
{
  struct list * new = (struct list *) malloc(sizeof(struct list));
  new->first = NULL;
  new->last  = NULL;
  new->size  = 0;
  return new;
}

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

/*******************************  Graph things. *******************************/
struct node{
  unsigned int id;
  struct list * neighbors;
};

struct graph{
  struct list * nodes;
  unsigned int size;
};

struct graph *new_graph() //UNTESTED
{
  struct graph *new = (struct graph *) malloc(sizeof(struct graph));
  new->nodes = new_list();
  new->size  = 0;
  return new;
}

struct node *create_node(unsigned int id, struct list * neig) //UNTESTED
{
  struct node *new = (struct node *) malloc(sizeof(struct node));
  new->id = id;
  new->neighbors = neig;
  return new;
}

void graph_add_node(struct graph *G, struct node *N) //UNTESTED
{
  list_add(G->nodes, N);
  G->size ++;
}

/******************************* Main function. *******************************/
int readfile(const char * filename, struct graph * G)
{
  FILE *fp = fopen(filename, "r");
  char ch  = '\0', 
       buffer[BUFFER_LEN] = "";
  int  i, id, *tmp;
  struct list *last_list;
  struct node *last_node;

  if(fp == NULL){
    fprintf(stderr,"No se puede leer el archivo \"%s\".\n", filename);
    return -1;
  }

  while (1) {
    i = 0;
    do {
      ch = getc(fp);
      if (ch == EOF) {
        return 0;
      } else if (ch == ':') {
//        printf("Creating node: [%s]\n", buffer);
        id = atoi(buffer);
        last_list = new_list();
        ch = getc(fp);
        if (ch == '\n'){
          break;
        }
        i = 0;
      } else if (ch == ' ' || ch == '\n') {
//        printf(">Vertex: [%s]\n", buffer);
        tmp = (int *) malloc(sizeof(int));
        buffer[i] = '\0';
        *tmp = atoi(buffer);
        list_add(last_list, tmp);
        i = 0;
      } else {
        buffer[i++] = ch;
      } 
    } while (ch != '\n');
    last_node = create_node(id, last_list);
    graph_add_node(G, last_node);
    last_node = NULL;
    last_list = NULL;
//    printf("Saving last node\n");
  }
}

int main(int argc, const char * args[])
{
  char *filename = (char*) args[1];
  printf("%s\n", filename);
  struct graph *G = new_graph();
  readfile(filename, G);

  struct list *ltmp;
  struct item *itmp, *i2tmp;
  struct node *ntmp;
  printf("Graph size: %d\n", G->size);
/*  for(itmp = G->nodes->first;
      itmp != NULL;
      itmp = itmp->next){
    ntmp = (struct node *) itmp->value;
    printf("Node id: %d\n  Neighbors:", ntmp->id );
    ltmp = ntmp->neighbors;
    for(i2tmp = ltmp->first;
        i2tmp != NULL;
        i2tmp = i2tmp->next){
      printf(" %d", *((int *) i2tmp->value));
    }
    printf("\n");
  }*/

  /* Cosas de listas
  struct list *my_list = new_list();
  for(i=0; i<max; i++){
    p = (int *) malloc(sizeof(int));
    *p = i;
    list_add(my_list, p);
  }
  // Recorrer una lista.
  struct item *tmp = my_list->first;
  while(tmp != NULL){
    printf("%d, ", *((int *) tmp->value));
    tmp = tmp->next;
  }*/
  return 0;
}

/* vim: set ts=2 sw=2 sts=2 tw=80 : */
