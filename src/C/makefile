FLAGS = -O3 -pthread
OBJS  = structures.c centrality.c threadpool.c main.c
HEAD  = structures.h centrality.h threadpool.h
NAME  = centrality

$(NAME): $(OBJS) $(HEAD)
	gcc $(FLAGS) -o $(NAME) $(OBJS)

debug: $(OBJS) $(HEAD)
	gcc $(FLAGS) -g -o $(NAME) $(OBJS)

