/*  SARbayes
 *  Author:     Jonathan Lee
 *  Date:       July 23, 2015
 */


#include <time.h>
#include "data.h"

#define LIMIT               100.0


double sigmoid(double y) {
    if(y > LIMIT) {
        return 1.0;
    }
    else if(y < -LIMIT) {
        return 0.0;
    }
    else {
        return 1/(1 + exp(-y));
    }
}


double calc_error(double *weights, table *data, size_t feature_count, 
        size_t *feature_indices, size_t class_index) {
    double input, sum, output, actual, error;
    size_t i, j, feature_index;
    instance inst;
    
    error = 0.0;
    for(i = 0; i < data->length; i++) {
        instance inst = data->instances[i];
        sum = weights[0];  // bias
        
        for(j = 0; j < feature_count; j++) {
            feature_index = feature_indices[j];
            input = *((double *)inst[feature_index]);
            if(!isnan(input)) {
                sum += weights[j + 1] * input;
            }
        }
        
        output = sigmoid(sum);
        actual = (double)(((char *)inst[class_index])[0] == 'D');
        error += pow(actual - output, 2);
    }
    
    return 0.5 * error;
}


void run_simulation(table *data, double delta) {
    FILE *fout = fopen("epoch-error.txt", "w+");
    
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
    
    feature_indices = realloc(feature_indices, feature_count * sizeof(double));
    double *new_weights = calloc(feature_count + 1, sizeof(double));
    double *weights = calloc(feature_count + 1, sizeof(double));
    double new_error, error = calc_error(
        weights, data, feature_count, feature_indices, class_index);
    
    long iteration = 0;
    while(error > 600) {
        printf("Epoch %lu: ", iteration);
        for(index = 0; index < feature_count + 1; index++) {
            printf("%f ", weights[index]);
            memcpy(new_weights, weights, (feature_count + 1) * sizeof(double));
            
            new_weights[index] += delta;
            new_error = calc_error(
                new_weights, data, feature_count, feature_indices, class_index);
            
            if(new_error < error) {
                error = new_error;
                weights[index] += delta;
            }
            else {
                weights[index] -= delta;
                error = calc_error(new_weights, data, 
                    feature_count, feature_indices, class_index);
            }
        }
        
        // sleep(1);
        printf("-> E = %f\n", error);
        fprintf(fout, "%f\n", error);
        iteration++;
    }
    
    fclose(fout);
}


int main(int argc, char **argv) {
    if(argc < 2) {
        printf("Usage: %s [filename]\n", argv[0]);
        return EXIT_FAILURE;
    }
    
    char *filename = argv[1];
    table *data = read_table(filename);
    run_simulation(data, 0.000001);
    
    return EXIT_SUCCESS;
}
