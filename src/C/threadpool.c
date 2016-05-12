#include <stdlib.h>
#include "threadpool.h"
#include "structures.h"

struct p_th *pth_create(unsigned int NTHREADS)
{
  struct p_th *P = (struct p_th*) malloc(sizeof(struct p_th));
  P->threads = (pthread_t*) malloc(sizeof(pthread_t)*NTHREADS);
  P->queue   = new_list();
  P->size    = NTHREADS;
  P->qmutex  = (sem_t*) malloc(sizeof(sem_t));
  P->st      = (sem_t*) malloc(sizeof(sem_t));
  P->qmutex  = (sem_t*) malloc(sizeof(sem_t));
  P->st      = (sem_t*) malloc(sizeof(sem_t));
  P->cmutex  = (pthread_mutex_t*) malloc(sizeof(pthread_mutex_t));
  P->idle    = (pthread_cond_t*) malloc(sizeof(pthread_cond_t));
  P->working = 0;
  sem_init(P->qmutex,0,1);
  sem_init(P->st,0,0);
  pthread_mutex_init(P->cmutex, NULL);
  pthread_cond_init(P->idle, NULL);
  int i;
  for (i = 0; i < NTHREADS; i++){
    pthread_create(&(P->threads[i]), NULL, _worker, P);
  }
  return P;
}

void pth_del(struct p_th *P)
{
  free(P->threads);
  list_del(P->queue);
  sem_destroy(P->qmutex);
  pthread_mutex_destroy(P->cmutex);
  pthread_cond_destroy(P->idle);
  sem_destroy(P->st);
  free(P->qmutex);
  free(P->cmutex);
  free(P->idle);
  free(P->st);
  free(P);
}

void *_worker(void *vp)
{
  int tmp;
  struct p_th *P = (struct p_th*) vp;
  struct job *my_job;
  while (1) {
    sem_wait(P->qmutex);
    if (P->queue->size != 0) {
      pthread_mutex_lock(P->cmutex);
      P->working++;
      pthread_mutex_unlock(P->cmutex);
      my_job = (struct job*) extract_first(P->queue);
      sem_post(P->qmutex);
      my_job->func(my_job->args);
      pthread_mutex_lock(P->cmutex);
      P->working--;
      if (!P->working)
        pthread_cond_signal(P->idle);
      pthread_mutex_unlock(P->cmutex);
    } else {
      sem_post(P->qmutex);
      sem_wait(P->st);
    }
  }
}

void pth_send_job(struct p_th *P, void *func, void *args)
{
  struct job *some_job = (struct job*) malloc(sizeof(struct job));
  some_job->func = func;
  some_job->args = args;
  sem_wait(P->qmutex);
  list_add(P->queue, some_job);
  sem_post(P->qmutex);
  sem_post(P->st);
}

void pth_wait(struct p_th *P)
{
  pthread_mutex_lock(P->cmutex);
  while (P->working || P->queue->size) {
    pthread_cond_wait(P->idle, P->cmutex);
  }
  pthread_mutex_unlock(P->cmutex);
}

/* vim: set ts=2 sw=2 sts=2 tw=80 : */
