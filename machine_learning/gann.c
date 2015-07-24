/*  SARbayes
 *  Author:     Jonathan Lee
 *  Date:       July 23, 2015
 */


#include <time.h>
#include "data.h"

#define LIMIT               100.0

typedef struct {
    unsigned long id;
    double *weights;
    double error;
} genome;


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


double drand(double min, double max) {
    assert(min < max);
    double diff = max - min;
    return (double)(diff * rand())/RAND_MAX + min;
}


genome *init_genome(size_t weight_count, double weight_min, double weight_max, 
        unsigned long id) {
    genome *individual = malloc(sizeof(genome));
    individual->weights = malloc(weight_count * sizeof(double));
    individual->id = id;
    
    size_t index;
    for(index = 0; index < weight_count; index++) {
        individual->weights[index] = drand(weight_min, weight_max);
    }
    
    individual->error = NAN;
    return individual;
}


void display_genome(genome *individual, size_t weight_count) {
    printf("[GID/%lu] W: ", individual->id);
    size_t index;
    for(index = 0; index < weight_count; index++) {
        printf("%.3f ", individual->weights[index]);
    }
    printf("-> E: %f\n", individual->error);
}


void evaluate(genome *individual, table *data, size_t *feature_indices, 
        size_t feature_count, size_t class_index) {
    size_t data_index, feature_index;
    instance inst;
    double sum, input, output, actual, error = 0.0;
    
    for(data_index = 0; data_index < data->length; data_index++) {
        inst = data->instances[data_index];
        sum = individual->weights[0];  // bias
        for(feature_index = 0; feature_index < feature_count; feature_index++) {
            input = *((double *)inst[feature_indices[feature_index]]);
            if(!isnan(input)) {
                sum += individual->weights[feature_index + 1] * input;
            }
        }
        output = sigmoid(sum);
        actual = (double)(((char *)inst[class_index])[0] == 'D');
        error += pow(actual - output, 2);
    }
    
    individual->error = 0.5*error;
}


int compare_individuals(const void *a, const void *b) {
    genome *_a = *((genome **)a), *_b = *((genome **)b);
    if(_a->error < _b->error) {
        return -1;
    }
    else if(_a->error > _b->error) {
        return 1;
    }
    else {
        return 0;
    }
}


genome **select_next_generation(genome **population, size_t pop_size, 
        double weight_min, double weight_max, size_t feature_count) {
    genome **tmp_population = malloc(pop_size * sizeof(genome *));
    genome *a, *b, *_a, *_b;
    size_t index, _index = 0;
    double error_sum = 0.0;
    
    for(index = 0; index < pop_size; index++) {
        a = tmp_population[index] = malloc(sizeof(genome));
        a->weights = malloc((feature_count + 1) * sizeof(double));
        error_sum += population[index]->error;
    }
    
    genome **subset = malloc(40 * sizeof(genome *));
    // Stochastic universal sampling
    for(index = 0; index < pop_size; index += pop_size / 40) {
        subset[_index++] = population[index];
    }
    
    
    /*
    double p;
    // Roulette wheel selection
    for(index = 0; index < pop_size; index++) {
        p = drand(0.0, 1.0);
        if(p < (1.0 - (population[index]->error)/error_sum)) {
            subset[_index++] = population[index];
        }
        if(_index == 40) {
            break;
        }
    }
    */
    
    assert(_index == 40);
    
    index = 0;
    size_t i, j, k, crossover;
    for(i = 0; i < 40; i++) {
        for(j = 0; j < i; j++) {
            a = subset[i], b = subset[j];
            _a = tmp_population[index], _b = tmp_population[index + 1];
            _a->id = index, _b->id = index + 1;
            crossover = 1 + rand()%feature_count;
            
            for(k = 0; k < feature_count + 1; k++) {
                if(k < crossover) {
                    _a->weights[k] = a->weights[k];
                    _b->weights[k] = b->weights[k];
                }
                else {
                    _a->weights[k] = b->weights[k];
                    _b->weights[k] = a->weights[k];
                }
            }
            
            index += 2;
        }
    }
    
    while(index < pop_size) {
        tmp_population[index] = init_genome(feature_count + 1, 
            weight_min, weight_max, index);
        index++;
    }
    
    assert(index == pop_size);
    
    // Mutation
    for(i = 0; i < pop_size; i++) {
        for(k = 0; k < feature_count + 1; k++) {
            if(rand() % 10 == 0) {
                tmp_population[i]->weights[k] = drand(weight_min, weight_max);
            }
        }
    }
    
    return tmp_population;
}


genome *run_simulation(table *data, long generation_count, size_t pop_size, 
        double weight_min, double weight_max) {
    size_t index, feature_count = 0, class_index = -1;
    size_t *feature_indices = malloc(data->column_count * sizeof(size_t));
    
    for(index = 0; index < data->column_count; index++) {
        if(data->column_types[index] == CONTINUOUS) {
            feature_indices[feature_count++] = index;
        }
        if(data->column_flags[index] == CLASS) {
            class_index = index;
        }
    }
    
    feature_indices = realloc(feature_indices, feature_count * sizeof(size_t));
    
    genome **population = malloc(pop_size * sizeof(genome *)), **tmp_population;
    for(index = 0; index < pop_size; index++) {
        population[index] = init_genome(
            feature_count + 1, weight_min, weight_max, index);
    }
    
    printf("\n");
    long generation = 0;
    while(generation < generation_count) {
        printf(">>> Generation %lu: \n", generation);
        for(index = 0; index < pop_size; index++) {
            evaluate(population[index], data, 
                feature_indices, feature_count, class_index);
        }
        
        qsort(population, pop_size, sizeof(genome *), &compare_individuals);
        for(index = 0; index < 10; index++) {
            display_genome(population[index], feature_count + 1);
        }
        
        // Critical
        tmp_population = select_next_generation(population, pop_size, 
            weight_min, weight_max, feature_count);
        free(population);
        population = tmp_population;
        
        printf("\n");
        generation++;
    }
    
    qsort(population, pop_size, sizeof(genome *), &compare_individuals);
    genome *best = malloc(sizeof(genome));
    memcpy(best, population[0], sizeof(genome));
    
    for(index = 0; index < pop_size; index++) {
        free(population[index]->weights);
        free(population[index]);
    }
    free(feature_indices);
    free(population);
    return best;
}


int main(int argc, char **argv) {
    if(argc < 2) {
        printf("Usage: %s [filename]\n", argv[0]);
        return EXIT_FAILURE;
    }
    
    printf("SARbayes GANN Survival Rate Simulation\n");
    printf("Seeding RNG ... \n");
    srand(time(NULL));
    char *filename = argv[1];
    
    printf("Reading table from %s ... \n", filename);
    table *data = read_table(filename);
    printf("Table address: %p\n", data);
    printf("Number of instances: %zu\n", data->length);
    
    printf("Running simulation ... \n");
    genome *best = run_simulation(data, 50, 2000, -1000.0, 1000.0);
    free(best);
    
    printf("Freeing memory ... \n");
    free_table(data);
    printf("Done.\n");
    return EXIT_SUCCESS;
}
