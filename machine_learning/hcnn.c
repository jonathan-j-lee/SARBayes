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


double run_network(double *weights, instance inst, size_t feature_count, 
        size_t *feature_indices, size_t class_index, double learning_rate) {
    double input, sum = weights[0], output, actual, error, delta;
    size_t index, feature_index;
    
    for(index = 0; index < feature_count; index++) {
        feature_index = feature_indices[index];
        input = *((double *)inst[feature_index]);
        if(!isnan(input)) {
            sum += weights[index + 1] * input;
        }
    }
    
    output = sigmoid(sum);
    actual = (double)(((char *)inst[class_index])[0] == 'D');
    error = 0.5*pow(output - actual, 2);
    
    for(index = 0; index < feature_count + 1; index++) {
        if(index == 0) {
            input = 1;
        }
        else {
            feature_index = feature_indices[index - 1];
            input = *((double *)inst[feature_index]);
        }
        
        // delta = learning_rate*input*(1 - input)*(input - output);
        // Delta rule (special case of backpropogation)
        delta = learning_rate*input*(actual - output)*output*(1 - output);
        if(!isnan(delta)) {
            weights[index] += delta;
        }
    }
    
    return error;
}


void run_simulation(table *data) {
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
    double *weights = calloc(feature_count + 1, sizeof(double));
    double learning_rate = 0.0001, error = 99999;
    // 0.0005 -> 373.7
    
    /*
    // Approximate weights
    weights[0] = -2.135869;
    weights[1] = 0.005530;
    weights[2] = 0.015483;
    weights[3] = -0.040691;
    weights[4] = 0.038882;
    weights[5] = -0.007324;
    weights[6] = -0.156527;
    weights[7] = -0.219943;
    */
    
    long epoch = 0;
    while(error > 10 && epoch < 1000000) {
        error = 0.0;
        for(index = 0; index < data->length; index++) {
            error += run_network(weights, data->instances[index], 
                feature_count, feature_indices, class_index, learning_rate);
        }
        
        printf("Epoch %lu: W -> ", epoch);
        for(index = 0; index < feature_count + 1; index++) {
            printf("%.8f ", weights[index]);
        }
        printf(" E -> %f\n", error);
        fprintf(fout, "%f\n", error);
        
        epoch++;
    }
    
    fclose(fout);
    
    /*
    size_t i, j;
    double input, sum, output, actual;
    size_t feature_index;
    instance inst;
    
    for(j = 0; j < data->length; j++) {
        inst = data->instances[j];
        sum = weights[0];
        for(i = 0; i < feature_count; i++) {
            feature_index = feature_indices[i];
            input = *((double *)inst[feature_index]);
            if(!isnan(input)) {
                sum += weights[index + 1] * input;
            }
        }
        
        output = sigmoid(sum);
        actual = (double)(((char *)inst[class_index])[0] == 'D');
        printf("%f %f\n", actual, output);
    }
    */
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
