/*  genetic.c
 *  SARbayes
 *  Bayesian Network Genetic Algorithm
 *  Author: Jonathan Lee
 *  Date: Jul. 21, 2015
 */


#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

const size_t BUF_SIZE = 1024;
size_t instance_count = 0;


typedef struct {
    // For identification purposes
    char *key;
    
    // Class (attribute to predict)
    char *status;
    
    // Subject predictors
    double age;
    char sex;
    char *category;
    double hours;
    
    // Weather predictors
    double temp_max;
    double temp_min;
    double wind_speed;
    double snow;
    double rain;
} instance;


void usage(FILE *stream, int argc, char **argv) {
    fprintf(stream, "Usage: %s [filename]\n", argv[0]);
}


instance *init_instance(void) {
    instance *current = malloc(sizeof(instance));
    assert(current != NULL);
    
    current->key        = NULL;
    current->status     = NULL;
    
    current->age        = NAN;
    current->sex        = '\0';
    current->category   = NULL;
    current->hours      = NAN;
    
    current->temp_max   = NAN;
    current->temp_min   = NAN;
    current->wind_speed = NAN;
    current->snow       = NAN;
    current->rain       = NAN;
    
    return current;
}


instance **read_instance_data(char *filename) {
    instance **instances = malloc(40000 * sizeof(instance *));
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
                current->status = strndup(buffer, index + 1);
                
                index = 0, column = 0;
                instances[instance_count++] = current;
                current = init_instance();
                break;
            case '\t':
                buffer[index] = '\0';
                switch(column++) {
                    case 0:
                        current->key = strndup(buffer, index + 1);
                        break;
                    case 1:
                        current->category = strndup(buffer, index + 1);
                        break;
                    case 2:
                        if(index > 0) {
                            current->age = atof(buffer);
                        }
                        break;
                    case 3:
                        current->sex = buffer[0];
                        break;
                    case 4:
                        if(index > 0) {
                            current->hours = atof(buffer);
                        }
                        break;
                    case 5:
                        if(index > 0) {
                            current->temp_max = atof(buffer);
                        }
                        break;
                    case 6:
                        if(index > 0) {
                            current->temp_min = atof(buffer);
                        }
                        break;
                    case 7:
                        if(index > 0) {
                            current->wind_speed = atof(buffer);
                        }
                        break;
                    case 8:
                        if(index > 0) {
                            current->snow = atof(buffer);
                        }
                        break;
                    case 9:
                        if(index > 0) {
                            current->rain = atof(buffer);
                        }
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


int main(int argc, char **argv) {
    if(argc < 2) {
        usage(stdout, argc, argv);
        return EXIT_FAILURE;
    }
    
    char *filename = argv[1];
    instance **instances = read_instance_data(filename);
    
    return EXIT_SUCCESS;
}
