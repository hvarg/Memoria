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
  //struct list * nodes;
  struct node ** nodes;
  unsigned int size;
};

struct graph *new_graph(unsigned int size)
{
  struct graph *new = (struct graph *) malloc(sizeof(struct graph));
  //new->nodes = new_list();
  new->nodes = (struct node **) malloc(sizeof(struct node *) * size);
  new->size  = size;
  return new;
}

struct node *create_node(unsigned int id, struct list * neig)
{
  struct node *new = (struct node *) malloc(sizeof(struct node));
  new->id = id;
  new->neighbors = neig;
  return new;
}

void graph_add_node(struct graph *G, struct node *N)
{
  //list_add(G->nodes, N);
  //G->size ++;
  G->nodes[N->id] = N;
}

/******************************* Main function. *******************************/
unsigned int count_lines(FILE * fp)
{
  char c = '\0';
  unsigned int n = 0;
  while ((c=getc(fp)) != EOF)
    if (c == '\n') n++;
  fseek(fp, 0, SEEK_SET);
  return n;
}

struct graph *file_to_graph(const char * filename)
{
  char ch  = '\0', 
       buffer[BUFFER_LEN] = "";
  unsigned int  i, id, size, *tmp;
  struct list *last_list;
  struct node *last_node;
  struct graph *G;

  FILE *fp = fopen(filename, "r");
  if(fp == NULL){
    fprintf(stderr,"No se puede leer el archivo \"%s\".\n", filename);
    return NULL;
  }

  size = count_lines(fp);
  G = new_graph(size);

  while (1) {
    i = 0;
    do {
      ch = getc(fp);
      if (ch == EOF) {
        fclose(fp);
        return G;
      } else if (ch == ':') {
        //printf("Creating node: [%s]\n", buffer);
        id = atoi(buffer);
        last_list = new_list();
        ch = getc(fp);
        if (ch == '\n'){
          break;
        }
        i = 0;
      } else if (ch == ' ' || ch == '\n') {
        //printf(">Vertex: [%s]\n", buffer);
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
    //printf("Saving last node (%d).\n", id);
  }
}

int main(int argc, const char * args[])
{
  char *filename = (char*) args[1];
  printf("%s\n", filename);
  struct graph *G = file_to_graph(filename);

  /*printf("Graph size: %d", G->size);
  int i, tid;
  struct list *list;
  struct item *item;
  for(i=0; i<G->size; i++){
    printf("\nNode id:%d (%x):\n\t", G->nodes[i]->id, &(G->nodes[i]));
    list = G->nodes[i]->neighbors;
    for(item=list->first; item != NULL; item = item->next){
      tid = *((int*) item->value);
      printf("%d(%x) ", tid, &(G->nodes[tid]));
    }
  }*/

  return 0;
}

/* vim: set ts=2 sw=2 sts=2 tw=80 : */
