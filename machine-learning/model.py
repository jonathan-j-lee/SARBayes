#!/usr/bin/env python2
# SARbayes/machine-learning/tree.py


import numpy as np
import Orange
import time

STATS_TEMPLATE = '''Statistics: 
    
    Model name: "{}"
    Runtime: {:.3f} s
    Evaluation method: Cross Validation
    Features: {}
    
    Predicted       Actual          Instances       
    ================================================
    Alive           Alive           {}              
    Alive           Dead            {}              
    Dead            Alive           {}              
    Dead            Dead            {}              
    
    Accuracy: {:.3f} %
'''


def cross_validate(data, learner, folds=10):
    rounded = int(np.ceil(len(data)/folds)*folds)
    increment = rounded // folds
    predictions = np.empty(len(data))
    
    for index in range(0, len(data), increment):
        lowerbound, upperbound = index, index + increment
        train_data = Orange.data.Table.from_table_rows(data, 
            list(range(lowerbound)) + list(range(upperbound, len(data)))
        )
        test_data = Orange.data.Table(data[lowerbound:upperbound])
        assert len(train_data) + len(test_data) == len(data)
        
        classifier = learner()(train_data)
        _predictions = classifier(test_data)
        for _index, _value in enumerate(_predictions):
            predictions[index + _index] = _value
    else:
        return predictions


def main():
    start_time = time.time()
    data = Orange.data.Table('ISRID')
    # Change learner as needed
    learner = Orange.classification.TreeLearner
    predictions = cross_validate(data, learner)
    
    confusion_matrix = np.zeros((2, 2))
    for case, predicted_status in zip(data, predictions):
        predicted_status = int(predicted_status)
        actual_status = int(case['status'].real)
        confusion_matrix[predicted_status, actual_status] += 1
    else:
        end_time = time.time()
    
    accuracy = 100*(confusion_matrix[0, 0] + confusion_matrix[1, 1])/len(data) 
    print(STATS_TEMPLATE.format(
        learner.name, 
        end_time - start_time, 
        ', '.join(attr.name for attr in data.domain.attributes), 
        int(confusion_matrix[0, 0]), 
        int(confusion_matrix[0, 1]), 
        int(confusion_matrix[1, 0]), 
        int(confusion_matrix[1, 1]), 
        accuracy
    ))


if __name__ == '__main__':
    main()
