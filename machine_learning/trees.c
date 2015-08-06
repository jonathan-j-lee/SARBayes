#include "data.h"


void make_tree(table *data) {
    
}


int main(int argc, char **argv) {
    if(argc < 2) {
        printf("Usage: %s [filename]\n", argv[0]);
        return EXIT_FAILURE;
    }
    
    char *filename = argv[1];
    table *data = read_table(filename);
    make_tree(data);
    
    return EXIT_SUCCESS;
}
