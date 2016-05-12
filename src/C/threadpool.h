#ifndef POOL_H_
#define POOL_H_

#include <pthread.h>
#include <semaphore.h>

struct p_th{
  pthread_t *threads;
  struct list *queue;
  unsigned int size, working;
  sem_t *qmutex, *st;
  pthread_mutex_t *cmutex;
  pthread_cond_t *idle;
};

struct job{
  void (*func)(void* args);
  void *args;
};

struct p_th *pth_create(unsigned int NTHREADS);
void pth_del(struct p_th *P);
void *_worker(void *vp);
void pth_send_job(struct p_th *P, void *func, void *args);
void pth_wait(struct p_th *P);

#endif
/* vim: set ts=2 sw=2 sts=2 tw=80 : */
