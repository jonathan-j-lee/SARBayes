/*  SARbayes
 *  Author:     Jonathan Lee
 *  Date:       July 26, 2015
 */


#include <time.h>
#include "data.h"


double drand(double min, double max) {
    assert(min < max);
    double diff = max - min;
    return (double)(diff * rand())/RAND_MAX + min;
}


void run_simulation(table *data) {
    size_t *feature_indices = malloc(data->column_count * sizeof(double));
    size_t index, class_index = -1, feature_count = 0;
    for(index = 0; index < data->column_count; index++) {
        if(data->column_types[index] == CONTINUOUS) {
            feature_indices[feature_count++] = index;
        }
        if(data->column_flags[index] == CLASS) {
            class_index = index;
        }
    }
    
    double *weights = malloc((feature_count + 1) * sizeof(double));
    for(index = 0; index < feature_count + 1; index++) {
        weights[index] = drand(-5.0, 5.0);
    }
}


int main(int argc, char **argv) {
    if(argc < 2) {
        printf("Usage: %s [filename]\n", argv[0]);
        return EXIT_FAILURE;
    }
    
    srand(time(NULL));
    char *filename = argv[1];
    table *data = read_table(filename);
    run_simulation(data);
    
    return EXIT_SUCCESS;
}
