#!/usr/bin/env python3
# SARbayes/machine_learning/hcnn.py


import math
import numpy as np
import Orange


def sigmoid(y, limit=100):
    if y > limit:
        return 1.0
    elif y < -limit:
        return 0.0
    else:
        return 1/(1 + math.exp(-y))


def main():
    data = Orange.data.Table('ISRID')
    features = list(feature for feature in data.domain.attributes 
        if feature.is_continuous)
    bias, weights = 0.0, np.zeros(len(features))
    learning_rate = 0.000001
    
    epoch = 0
    while epoch < 100:
        error = 0.0
        for instance in data:
            transfer = bias + np.dot(weights, values)
            for weight, feature in zip(weights, features):
                value = instance[feature.name].value
                if not math.isnan(value):
                    transfer += weight * value
            prediction = sigmoid(transfer)
            actual = instance.get_class()._value
            
            for index, feature in enumerate(features):
                value = instance[feature.name].value
                if not math.isnan(value):
                    delta = (learning_rate * value * (actual - prediction) * 
                        prediction * (1 - prediction))
                    weights[index] += delta
            
            error += pow(prediction - actual, 2)
        error *= 0.5
        print(weights, error)
        epoch += 1


if __name__ == '__main__':
    main()
