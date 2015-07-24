/*  SARbayes
 *  Author:     Jonathan Lee
 *  Date:       July 23, 2015
 */


#ifndef DATA_H_
#define DATA_H_

#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_INSTANCE_COUNT  40000
#define MAX_INSTANCE_SIZE   256
#define DELIMETER           "\t"

enum types {
    DISCRETE, CONTINUOUS, STRING
};

enum flags {
    META, CLASS, FEATURE
};

typedef void **instance;

typedef struct {
    instance *instances;
    size_t length;
    
    // Header metadata
    size_t column_count;
    char **column_names;
    int *column_types;
    int *column_flags;
} table;


size_t get_column_count(const char buffer[]);

void read_header(const char buffer[], table *data, const size_t row);

instance read_instance(const char buffer[], table *data);

table *read_table(char *filename);

void summary(table *data, size_t tab_count, size_t start, size_t stop);

void free_table(table *data);

#endif
