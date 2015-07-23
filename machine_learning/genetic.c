/*  genetic.c
 *  SARbayes
 *  Neural Network Genetic Algorithm
 *  Author: Jonathan Lee
 *  Date: Jul. 21, 2015
 */


#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <time.h>

const size_t BUF_SIZE               = 1024;
const size_t MAX_INSTANCE_COUNT     = 40000;
const size_t POP_SIZE               = 2000;
const int N_WEIGHTS                 = 7;
const int W_MAX                     = 100;
const int W_MIN                     = -100;
size_t instance_count               = 0;


enum Sex {
    MALE, FEMALE
};

enum Status {
    DEAD, ALIVE
};


typedef struct {
    // For identification purposes
    char *key;
    
    // Class (attribute to predict)
    int status;
    
    // Subject predictors
    double age;
    int sex;
    char *category;
    double hours;
    
    // Weather predictors
    double temp_max;
    double temp_min;
    double wind_speed;
    double snow;
    double rain;
} instance;

typedef struct {
    double weights[7];
    double error;
} individual;

typedef int (*classifier)(instance *);


void usage(FILE *stream, int argc, char **argv) {
    fprintf(stream, "Usage: %s [filename]\n", argv[0]);
}


instance *init_instance(void) {
    instance *current = malloc(sizeof(instance));
    assert(current != NULL);
    
    current->key        = NULL;
    current->category   = NULL;
    
    return current;
}


instance **read_instance_data(char *filename) {
    instance **instances = malloc(MAX_INSTANCE_COUNT * sizeof(instance *));
    instance *current = init_instance();
    
    char buffer[BUF_SIZE];
    char tmp;
    size_t index = 0, column = 0, header = 0;
    
    FILE *fin = fopen(filename, "r");
    assert(instances != NULL && fin != NULL);
    
    while((tmp = fgetc(fin)) != EOF && header < 3) {
        if(tmp == '\n') {
            header++;
        }
    }
    
    while((tmp = fgetc(fin)) != EOF) {
        switch(tmp) {
            case '\n':
                assert(column == 10);
                buffer[index] = '\0';
                current->status = strcmp(buffer, "DEAD") == 0 ? DEAD : ALIVE;
                
                index = 0, column = 0;
                instances[instance_count++] = current;
                current = init_instance();
                break;
            case '\t':
                buffer[index] = '\0';
                switch(column++) {
                    case 0:
                        current->key        = strndup(buffer, index + 1);
                        break;
                    case 1:
                        current->category   = strndup(buffer, index + 1);
                        break;
                    case 2:
                        current->age        = index > 0 ? atof(buffer) : NAN;
                        break;
                    case 3:
                        current->sex        = buffer[0] == 'M' ? MALE : 
                                              (buffer[0] == 'F' ? FEMALE : -1);
                        break;
                    case 4:
                        current->hours      = index > 0 ? atof(buffer) : NAN;
                        break;
                    case 5:
                        current->temp_max   = index > 0 ? atof(buffer) : NAN;
                        break;
                    case 6:
                        current->temp_min   = index > 0 ? atof(buffer) : NAN;
                        break;
                    case 7:
                        current->wind_speed = index > 0 ? atof(buffer) : NAN;
                        break;
                    case 8:
                        current->snow       = index > 0 ? atof(buffer) : NAN;
                        break;
                    case 9:
                        current->rain       = index > 0 ? atof(buffer) : NAN;
                        break;
                }
                index = 0;
                break;
            default:
                buffer[index++] = tmp;
                assert(index < BUF_SIZE);
        }
    }
    
    free(current);
    fclose(fin);
    return instances;
}


double log_sigmoid(double y) {
    if(y > 100) {
        return 1.0;
    }
    if(y < -100) {
        return 0.0;
    }
    return 1/(1 + exp(-y));
}


int compare(const void *a, const void *b) {
    individual _a = *((individual *)a), _b = *((individual *)b);
    if(_a.error < _b.error) {
        return -1;
    }
    else if(_a.error > _b.error) {
        return 1;
    }
    else {
        return 0;
    }
}


double predict(instance *current, individual indv) {
    double s = 0.0;
    if(!isnan(current->age)) {
        s += indv.weights[0]*current->age;
    }
    if(!isnan(current->hours)) {
        s += indv.weights[1]*current->hours;
    }
    if(!isnan(current->temp_max)) {
        s += indv.weights[2]*current->temp_max;
    }
    if(!isnan(current->temp_min)) {
        s += indv.weights[3]*current->temp_min;
    }
    if(!isnan(current->snow)) {
        s += indv.weights[4]*current->snow;
    }
    if(!isnan(current->rain)) {
        s += indv.weights[5]*current->rain;
    }
    s += indv.weights[6];
    return log_sigmoid(s);
}


void evaluate(instance **instances, 
        size_t instance_count, individual *population) {
    size_t i, j, k;
    double e, p, a;
    instance *current;
    
    for(i = 0; i < POP_SIZE; i++) {
        e = 0.0;
        for(j = 0; j < instance_count; j++) {
            current = instances[j];
            p = predict(current, population[i]);
            a = current->status == ALIVE ? 1 : 0;
            e += pow(p - a, 2);
        }
        population[i].error = 0.5*e;
    }
}


double random_double(double lowerbound, double upperbound) {
    return ((double)rand() / 
        (double)(RAND_MAX/(upperbound - lowerbound))) + lowerbound;
}


individual *breed(individual *population) {
    individual *nextgen = malloc(POP_SIZE * sizeof(individual));
    assert(nextgen != NULL);
    individual other, fittest = population[0];
    size_t i, j, k = 0;
    size_t crossover;
    
    for(i = 1; i < POP_SIZE/2 + 1; i++) {
        other = population[i];
        crossover = rand()%6 + 1;  // int between 1 and 6, inclusive
        
        for(j = 0; j < N_WEIGHTS; j++) {
            if(j < crossover) {
                nextgen[k].weights[j] = fittest.weights[j];
                nextgen[k + 1].weights[j] = other.weights[j];
            }
            else {
                nextgen[k].weights[j] = other.weights[j];
                nextgen[k + 1].weights[j] = fittest.weights[j];
            }
            
            // mutation
            int g;
            for(g = 0; g < 2; g++) {
                if(rand()%10 == 0) {
                    nextgen[k].weights[rand()%N_WEIGHTS] = \
                        random_double(W_MIN, W_MAX);
                }
                if(rand()%10 == 0) {
                    nextgen[k + 1].weights[rand()%N_WEIGHTS] = \
                        random_double(W_MIN, W_MAX);
                }
            }
        }
        
        k += 2;
    }
    
    return nextgen;
}


void run_simulation(instance **instances, size_t instance_count, 
        long max_generation) {
    individual *population = malloc(POP_SIZE * sizeof(individual));
    size_t i, j;
    
    for(i = 0; i < POP_SIZE; i++) {
        for(j = 0; j < N_WEIGHTS; j++) {
            population[i].weights[j] = random_double(W_MIN, W_MAX);
            assert(W_MIN <= population[i].weights[j] && 
                population[i].weights[j] <= W_MAX);
        }
    }
    
    long generation = 0;
    while(generation < max_generation) {
        evaluate(instances, instance_count, population);
        qsort(population, POP_SIZE, sizeof(individual), &compare);
        
        printf("Generation %lu: \n", generation);
        for(i = 0; i < 10; i++) {
            printf("  ");
            for(j = 0; j < N_WEIGHTS; j++) {
                printf("%f ", population[i].weights[j]);
            }
            printf("-> E = %f\n", population[i].error);
        }
        
        individual *nextgen = breed(population);
        free(population);
        population = nextgen;
        generation++;
    }
    
    evaluate(instances, instance_count, population);
    qsort(population, POP_SIZE, sizeof(individual), &compare);
    individual best = population[0];
    size_t index;
    long correct = 0;
    int _a, _p;
    for(index = 0; index < instance_count; index++) {
        double p = predict(instances[index], best);
        _p = p < 0.25 ? 0 : (p > 0.75 ? 1 : -1);
        if(_p == -1) {
            continue;
        }
        _a = instances[index]->status == ALIVE ? 1 : 0;
        correct += (_p == _a);
    }
    printf("Number correct: %lu\n", correct);
    printf("Accuracy: %f\n", (double)correct/instance_count);
    
    free(population);
}


int main(int argc, char **argv) {
    if(argc < 2) {
        usage(stdout, argc, argv);
        return EXIT_FAILURE;
    }
    
    srand(time(NULL));
    printf("Reading instance data ... \n");
    char *filename = argv[1];
    instance **instances = read_instance_data(filename);
    printf("Number of instances: %zu\n", instance_count);
    
    run_simulation(instances, instance_count, 50);
    
    size_t index;
    for(index = 0; index < instance_count; index++) {
        free(instances[index]->key);
        free(instances[index]->category);
    }
    free(instances);
    printf("Done.\n");
    return EXIT_SUCCESS;
}
