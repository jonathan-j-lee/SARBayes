#!/usr/bin/env python2
# SARbayes/machine_learning/evaluate.py


import copy
import numpy as np
import Orange, Orange.base
import random
import sys
import time

STATS_TEMPLATE = '''Statistics: 
    
    Model name: "{}"
    Runtime: {:.3f} s
    Evaluation method: Cross Validation
    Features: {}
    
    Predicted       Actual          Instances       
    ================================================
    {}
    
    Accuracy: {:.3f} %
'''


class CaseBasedLearner(Orange.base.Learner):
    """ Case-Based Learner """
    name = 'case-based learner'
    
    def __init__(self):
        self._probabilities = dict()
    
    def __call__(self, train_data):
        # attr -> feature
        
        class_names = get_class_names(train_data)
        for attr in train_data.domain.attributes:
            self._probabilities[attr.name] = dict()
            col_values = list(filter(
                lambda value: not np.isnan(value), 
                list(instance[attr.name]._value for instance in train_data)
            ))
            
            if attr.is_continuous:
                _min, _max = min(col_values), max(col_values)
                _step, _prev = abs(_max - _min)/10, _min
                
                for _next in np.arange(_min + _step, _max + 1e-3, _step):
                    key = _prev, _next
                    
                    if key not in self._probabilities[attr.name]:
                        self._probabilities[attr.name][key] = [0, 0]
                    
                    _prev = _next
            elif attr.is_discrete:
                for key in set(int(value) for value in col_values):
                    self._probabilities[attr.name][key] = [0, 0]
            else:
                raise ValueError
        
        for instance in train_data:
            status = instance.get_class().value
            for attr in instance.domain.attributes:
                value = instance[attr.name]._value
                if np.isnan(value):  # Missing attribute
                    continue
                
                if attr.is_continuous:
                    for key in self._probabilities[attr.name]:
                        lowerbound, upperbound = key
                        if lowerbound < value <= upperbound:
                            self._probabilities[attr.name][key][1] += 1
                            if status == 'DEAD':
                                self._probabilities[attr.name][key][0] += 1
                            break
                
                elif attr.is_discrete:
                    value = int(value)
                    self._probabilities[attr.name][value][1] += 1
                    if status == 'DEAD':
                        self._probabilities[attr.name][value][0] += 1
                
                else:
                    raise ValueError
        
        def classifier(test_data):
            _p = list()
            for instance in test_data:
                p = 1  # P(DOA)
                for attr in instance.domain.attributes:
                    value = instance[attr.name]._value
                    if np.isnan(value):  # Missing attribute
                        continue
                    
                    if attr.is_continuous:
                        for key in self._probabilities[attr.name]:
                            lowerbound, upperbound = key
                            if lowerbound < value <= upperbound:
                                n_doa, n_lost = \
                                    self._probabilities[attr.name][key]
                                assert n_doa <= n_lost
                                if n_lost > 0:
                                    p *= n_doa/n_lost
                                break
                    
                    elif attr.is_discrete:
                        value = int(value)
                        n_doa, n_lost = self._probabilities[attr.name].get(
                            value, (1, 1))
                        assert n_doa <= n_lost
                        if n_lost > 0:
                            p *= n_doa/n_lost
                    
                    else:
                        raise ValueError
                else:
                    _p.append(p)
            else:
                return np.array([class_names['ALIVE'] if p < 0.025  # Threshold
                    else class_names['DEAD'] for p in _p])
        
        return classifier


class LinearRegressionLearner(Orange.base.Learner):
    name = 'linear regression learner'
    
    def __init__(self):
        self.coefficients = {
            'HighTemp': (0.2149, 86.18), 
            'LowTemp': (0.2416, 88.37), 
            'WindSpeed': (-0.03717, 90.77)
        }
    
    def __call__(self, training_data):
        def classifier(testing_data):
            states = []
            
            for instance in testing_data:
                p = []
                for name, (m, b) in self.coefficients.items():
                    if not np.isnan(instance[name]):
                        p.append(m*instance[name] + b)
                if len(p) == 0:
                    states.append(0.0)  # ALIVE
                else:
                    if np.mean(p)/100 < 0.88:
                        states.append(1.0)  # DEAD
                    else:
                        states.append(0.0)  # ALIVE
            
            return states
        
        return classifier


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
        
        #classifier = learner(min_samples_leaf=150)(train_data)
        classifier = learner()(train_data)
        _predictions = classifier(test_data)
        for _index, _value in enumerate(_predictions):
            predictions[index + _index] = _value
    else:
        return predictions


def get_class_names(data):
    classes = set(instance.get_class() for instance in data)
    return {class_type.value: int(class_type._value) for class_type in classes}


def get_confusion_matrix(data, predictions):
    class_names = get_class_names(data)
    n_classes = len(class_names)
    confusion_matrix = np.zeros((n_classes, n_classes))
    
    for instance, predicted_class in zip(data, predictions):
        actual_class = instance.get_class()._value
        confusion_matrix[int(predicted_class), int(actual_class)] += 1
    else:
        return confusion_matrix


def print_statistics(data, learner, confusion_matrix, _file=sys.stdout):
    start = time.time()
    end = time.time()
    class_names = get_class_names(data)
    
    correct = 0
    for index in range(confusion_matrix.shape[0]):
        correct += confusion_matrix[index, index]
    else:
        accuracy = 100*correct/len(data)
    
    print(STATS_TEMPLATE.format(
        learner.name, 
        end - start, 
        ', '.join(attr.name for attr in data.domain.attributes), 
        '\n    '.join(row_name.ljust(16) + col_name.ljust(16) + 
            str(int(
                confusion_matrix[int(row_value), int(col_value)])).ljust(16) 
            for row_name, row_value in class_names.items()
            for col_name, col_value in class_names.items()
        ), 
        accuracy
    ), file=_file)


def main():
    data = Orange.data.Table('ISRID-survival')
    
    #indices = np.array([index for index, instance in enumerate(data) 
    #    if instance.get_class()._value == 1.0 or random.random() < 0.1])
    #data = Orange.data.Table.from_table_rows(data, indices)
    
    learner = Orange.classification.MajorityLearner
    print_statistics(data, learner, get_confusion_matrix(data, cross_validate(data, learner)))
    
    learner = Orange.classification.RandomForestLearner
    print_statistics(data, learner, get_confusion_matrix(data, cross_validate(data, learner)))
    #print_statistics(data, learner, get_confusion_matrix(data, cross_validate(data, learner)))
    
    #classifier = learner(data)
    #print(cross_validate(data, learner))
    #print_statistics(data, learner, get_confusion_matrix(data, classifier(data)))
    
    #learner = learner()(data)
    #print(learner)
    
    """
    final_predictions = np.empty(len(data))
    predictions = tuple(
        cross_validate(data, learner) for learner in (
            Orange.classification.LogisticRegressionLearner, 
            Orange.classification.NaiveBayesLearner, 
            Orange.classification.TreeLearner, 
            CaseBasedLearner
        )
    )
    
    for index, instance in enumerate(data):
        s = sum(prediction[index] for prediction in predictions)
        final_predictions[index] = 1.0 if s >= 1 else 0.0
        
        # p = tuple(prediction[index] for prediction in predictions)
        # final_predictions[index] = max(set(p), key=p.count)
    
    print_statistics(data, Orange.classification.TreeLearner, get_confusion_matrix(data, final_predictions))
    """


if __name__ == '__main__':
    main()
