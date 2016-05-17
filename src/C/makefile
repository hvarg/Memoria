FLAGS = -O3 -g -pthread
OBJS  = structures.c centrality.c threadpool.c main.c
HEAD  = structures.h centrality.h threadpool.h
NAME  = centrality

$(NAME): $(OBJS) $(HEAD)
	gcc $(FLAGS) -o $(NAME) $(OBJS)

test: structures.c ex.c threadpool.c structures.h threadpool.h
	gcc -pthread -o ex structures.c ex.c threadpool.c

para: structures.c main.c threadpool.c structures.h threadpool.h centrality_p.c centrality_p.h
	gcc -g -pthread -o para structures.c main.c threadpool.c centrality_p.c
