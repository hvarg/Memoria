#include <stdio.h>
#include <stdlib.h>
#include <string.h> // solo por memcpy
#include "structures.h"
#include "centrality.h"

#define BUFFER_LEN 8

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
       buffer[BUFFER_LEN] = ""; //se puede calcular por el nro de lineas.
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
        memset(buffer, 0, BUFFER_LEN);
      } else if (ch == ' ' || ch == '\n') {
        //printf(">Vertex: [%s]\n", buffer);
        tmp = (int *) malloc(sizeof(int));
        buffer[i] = '\0';
        *tmp = atoi(buffer);
        list_add(last_list, tmp);
        i = 0;
        memset(buffer, 0, BUFFER_LEN);
      } else {
        buffer[i++] = ch;
      } 
    } while (ch != '\n');
    last_node = new_node(id, last_list);
    graph_add_node(G, last_node);
    last_node = NULL;
    last_list = NULL;
    //printf("Saving last node (%d).\n", id);
  }
}

int main(int argc, const char * args[])
{
  char *filename = (char*) args[1];
  //printf("%s\n", filename);
  struct graph *G = file_to_graph(filename);
  float *BC = betweenness_centrality(G);

  //printf("Graph size: %d", G->size);
  /*int i, tid;
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

  char *out = (char *) malloc(sizeof(char) * (strlen(filename) + 8));
  strcpy(out, filename);
  strcat(out, ".result");
  FILE *fo = fopen(out, "w");
  int i;
  for (i=0; i< G->size; i++){
    fprintf(fo,"%d: %f\n", i, BC[i]);
  }
  fclose(fo);

  graph_del(G);
  free(BC);
  return EXIT_SUCCESS;
}

/* vim: set ts=2 sw=2 sts=2 tw=80 : */
