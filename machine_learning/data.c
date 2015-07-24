/*  SARbayes
 *  Author:     Jonathan Lee
 *  Date:       July 23, 2015
 */


#include "data.h"


size_t get_column_count(const char buffer[]) {
    size_t column_count = 0;
    char *token, *buffer_copy = strdup(buffer);
    
    while((token = strsep(&buffer_copy, DELIMETER)) != NULL) {
        column_count++;
    }
    
    free(token);
    free(buffer_copy);
    return column_count;
}


void read_header(const char buffer[], table *data, const size_t row) {
    char *token, *buffer_copy = strdup(buffer);
    size_t column = 0;
    int value;
    
    while((token = strsep(&buffer_copy, DELIMETER)) != NULL) {
        switch(row) {
            case 0:
                data->column_names[column] = strdup(token);
                break;
            case 1:
                switch(token[0]) {
                    case 'd':
                        value = DISCRETE;
                        break;
                    case 'c':
                        value = CONTINUOUS;
                        break;
                    default:
                        value = STRING;
                }
                data->column_types[column] = value;
                break;
            case 2:
                switch(token[0]) {
                    case 'm':
                        value = META;
                        break;
                    case 'c':
                        value = CLASS;
                        break;
                    default:
                        value = FEATURE;
                }
                data->column_flags[column] = value;
                break;
            default:
                assert(0);
        }
        column++;
    }
    
    free(token);
    free(buffer_copy);
    assert(column == data->column_count);
}


instance read_instance(const char buffer[], table *data) {
    instance inst = malloc(data->column_count * sizeof(void *));
    char *token, *buffer_copy = strdup(buffer);
    size_t column = 0;
    double *tmp;
    
    while((token = strsep(&buffer_copy, DELIMETER)) != NULL) {
        switch(data->column_types[column]) {
            case DISCRETE:
                inst[column] = (void *)strdup(token);
                break;
            case CONTINUOUS:
                tmp = malloc(sizeof(double));
                *tmp = strlen(token) > 0 ? atof(token) : NAN;
                inst[column] = tmp;
                break;
            case STRING:
                inst[column] = (void *)strdup(token);
                break;
            default:
                assert(0);
        }
        column++;
    }
    
    free(token);
    free(buffer_copy);
    return inst;
}


table *read_table(char *filename) {
    FILE *fp = fopen(filename, "r");
    table *data = malloc(sizeof(table));
    assert(fp != NULL && data != NULL);
    
    data->instances = malloc(MAX_INSTANCE_COUNT * sizeof(instance));
    data->length = 0;
    instance inst;
    
    char buffer[MAX_INSTANCE_SIZE];
    char tmp;
    size_t row = 0, index = 0;
    
    while((tmp = fgetc(fp)) != EOF) {
        if(tmp == '\n') {
            buffer[index] = '\0';
            switch(row) {
                case 0:
                    data->column_count = get_column_count(buffer);
                    data->column_names = malloc(
                        data->column_count * sizeof(char *));
                    data->column_types = malloc(
                        data->column_count * sizeof(int));
                    data->column_flags = malloc(
                        data->column_count * sizeof(int));
                case 1:
                case 2:
                    read_header(buffer, data, row);
                    break;
                default:
                    inst = read_instance(buffer, data);
                    assert(data->length < MAX_INSTANCE_COUNT && inst != NULL);
                    data->instances[data->length++] = inst;
                    break;
            }
            
            index = 0;
            row++;
        }
        else {
            buffer[index++] = tmp;
            assert(index < MAX_INSTANCE_SIZE);
        }
    }
    
    fclose(fp);
    size_t bytes_used = data->length * sizeof(instance);
    data->instances = realloc(data->instances, bytes_used);
    return data;
}


void summary(table *data, size_t tab_count, size_t start, size_t stop) {
    size_t index, column;
    int type, flag;
    
    char *tabs = malloc(tab_count * sizeof(char) + 1);
    for(index = 0; index < tab_count; index++) {
        tabs[index] = '\t';
    }
    tabs[index] = '\0';
    
    for(column = 0; column < data->column_count; column++) {
        printf("%s%s", data->column_names[column], tabs);
    }
    printf("\n");
    
    for(column = 0; column < data->column_count; column++) {
        type = data->column_types[column];
        printf("%s%s", type == DISCRETE ? "discrete" : (
            type == CONTINUOUS ? "continuous" : "string"), tabs);
    }
    printf("\n");
    
    for(column = 0; column < data->column_count; column++) {
        flag = data->column_flags[column];
        printf("%s%s", flag == META ? "meta" : (
            flag == CLASS ? "class" : ""), tabs);
    }
    printf("\n");
    
    instance inst;
    void *value;
    double *tmp;
    
    for(index = 0; index < data->length; index++) {
        if(start <= index && index < stop) {
            inst = data->instances[index];
            for(column = 0; column < data->column_count; column++) {
                type = data->column_types[column];
                value = inst[column];
                
                switch(type) {
                    case DISCRETE:
                        printf("%s", (char *)value);
                        break;
                    case CONTINUOUS:
                        tmp = (double *)value;
                        if(!isnan(*tmp)) {
                            printf("%f", *tmp);
                        }
                        break;
                    default:
                        printf("%s", (char *)value);
                }
                
                printf("%s", tabs);
            }
            printf("\n");
        }
    }
}


void free_table(table *data) {
    if(data != NULL) {
        size_t index, column;
        for(index = 0; index < data->column_count; index++) {
            free(data->column_names[index]);
        }
        
        instance inst;
        for(index = 0; index < data->length; index++) {
            inst = data->instances[index];
            for(column = 0; column < data->column_count; column++) {
                free(inst[column]);
            }
            free(inst);
        }
        
        // Free struct members
        free(data->instances);
        free(data->column_names);
        free(data->column_types);
        free(data->column_flags);
        
        // Free top-level pointer
        free(data);
    }
}
