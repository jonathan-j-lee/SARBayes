#!/usr/bin/env python3
# SARbayes/machine_learning/tree.py


import Orange
import evaluation


class CustomTreeLearner(Orange.classification.Learner):
    def __init__(self, 
            base_learner=Orange.classification.TreeLearner, 
            name='CustomTreeLearner'):
        self.base_learner, self.name = base_learner, name
    def __call__(self):
        pass


def main():
    data = Orange.data.Table('ISRID')
    learner = CustomLearner


if __name__ == '__main__':
    main()
