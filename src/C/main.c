#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "structures.h"
#include "centrality.h"
#include "threadpool.h"

#define BUFFER_LEN 8

/* Aqui se guardaran los segmentos a calcular y su resultado. */
struct data{
  int   init, end;
  float *bc;
};

/* Se declara el grafo como global para facilitar el acceso. */
struct graph *G;
int *IDC, *ODC;

/* Cuenta las lineas del archivo apuntado por fp y pone el cursor al principio
 * del archivo.
 * Retorno: numero de lineas de fp. */
unsigned int count_lines(FILE * fp)
{
  char c = '\0';
  unsigned int n = 0;
  while ((c=getc(fp)) != EOF)
    if (c == '\n') n++;
  fseek(fp, 0, SEEK_SET);
  return n;
}

/* Abre el archivo `filename` y crea un grafo con la lista de adyacencia
 * inscrita en el. Cada linea del archivo debe cumplir la siguiente expresion
 * regular (con BL como el BUFFER_LEN): '\d{1,BL}:( \d{1,BL})*\n'
 * Retorno: Un grafo G (descrito en structures.h)*/
struct graph *file_to_graph(const char * filename)
{
  char ch  = '\0', 
       buffer[BUFFER_LEN] = ""; // Se puede calcular por el nro de lineas.
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
  IDC = (int*) calloc(size, sizeof(int));
  ODC = (int*) malloc(size * sizeof(int));

  while (1) {
    i = 0;
    do {
      ch = getc(fp);
      if (ch == EOF) {
        fclose(fp);
        return G;
      } else if (ch == ':') {
        id = atoi(buffer);
        last_list = new_list();
        ch = getc(fp);
        if (ch == '\n'){
          break;
        }
        i = 0;
        memset(buffer, 0, BUFFER_LEN);
      } else if (ch == ' ' || ch == '\n') {
        tmp = (int *) malloc(sizeof(int));
        buffer[i] = '\0';
        *tmp = atoi(buffer);
        list_add(last_list, tmp);
        IDC[*tmp]++;
        i = 0;
        memset(buffer, 0, BUFFER_LEN);
      } else {
        buffer[i++] = ch;
      } 
    } while (ch != '\n');
    ODC[id] = last_list->size;
    last_node = new_node(id, last_list);
    graph_add_node(G, last_node);
    last_node = NULL;
    last_list = NULL;
  }
}

/* Trabajo que hara cada thread. Calcula una parte de la centralidad total. */
void *__cent(void *DT)
{
  struct data *dt = (struct data*) DT;
  dt->bc = betweenness_centrality_range(G, dt->init, dt->end);
}

int main(int argc, const char * args[])
{
  if (argc < 2) {
    printf("Modo de uso: ./centrality archivo.sg [#threads]\n");
    return EXIT_SUCCESS;
  }
  char  *filename = (char*) args[1]; 
  printf("File: %s\n", filename);
  int   NT = (argc > 2) ? atoi(args[2]) : 4,
        i, j, gap;
  float *BC;
  struct data  **D;
  struct p_th  *P;

  if ( (G = file_to_graph(filename)) == NULL) 
    return EXIT_FAILURE;
  if (NT > 1) {
    printf("Threads: %d\n", NT);
    gap = (G->size%NT == 0) ? G->size/NT : (G->size/NT)+1;
    BC  = (float*) malloc(sizeof(float) * G->size);
    D   = (struct data**) malloc(sizeof(struct data*)*NT);
    P   = pth_create(NT);

    for (i = 0; i < NT; i++) {
      D[i] = (struct data*) malloc(sizeof(struct data));
      D[i]->init = i*gap;
      D[i]->end  = (i+1)*gap;
      D[i]->bc   = (float*) malloc(sizeof(float) * G->size);
    }

    for (i = 0; i < NT; i++) {
      pth_send_job(P, __cent, D[i]);
    }
    pth_wait(P);

    for (i = 0; i < G->size; i++) { //se puede acumular todo en el primero.
      BC[i] = 0.0;
      for (j = 0; j < NT; j++) {
        BC[i] += D[j]->bc[i];
      }
    }
    pth_del(P);
    for (i = 0; i < NT; i++) {
      free(D[i]->bc);
      free(D[i]);
    }
    free(D);
  } else {
    printf("Threads: Single core\n");
    BC = betweenness_centrality(G);
  }

  /* Guardando los resultados en archivos. */
  short fn_size = strlen(filename);
  char *bc_out  = (char *) malloc(sizeof(char) * (fn_size + 11)),
       *idc_out = (char *) malloc(sizeof(char) * (fn_size + 12)),
       *odc_out = (char *) malloc(sizeof(char) * (fn_size + 12));
  strcpy(bc_out, filename);
  strcpy(idc_out, filename);
  strcpy(odc_out, filename);
  strcat(bc_out, ".bc.result");
  strcat(idc_out, ".idc.result");
  strcat(odc_out, ".odc.result");
  FILE *fbc = fopen(bc_out, "w"),
       *fidc = fopen(idc_out, "w"),
       *fodc = fopen(odc_out, "w");
  for (i=0; i< G->size; i++){
    fprintf(fbc,"%d: %f\n", i, BC[i]);
    fprintf(fidc,"%d: %d\n", i, IDC[i]);
    fprintf(fodc,"%d: %d\n", i, ODC[i]);
  }
  fclose(fbc);
  fclose(fidc);
  fclose(fodc);
  free(bc_out);
  free(idc_out);
  free(odc_out);

  graph_del(G);
  free(BC);
  free(IDC);
  free(ODC);
  return EXIT_SUCCESS;
}

/* vim: set ts=2 sw=2 sts=2 tw=80 : */
