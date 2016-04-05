#!/usr/bin/env python3

"""
bayes
=====
"""

import logging
import math

from sqlalchemy import and_, or_
from sqlalchemy.orm.attributes import InstrumentedAttribute

import database
from database.models import Subject, Group, Point, Location, Weather
from database.models import Operation, Outcome, Search, Incident
from database.processing import survival_rate

from merge import initialize_logging


class Interval:
    """ A continuous interval on the number line. """

    def __init__(self, left, right, include=(True, True)):
        if left > right:
            raise ValueError('left bound is greater than the right bound')

        include_left, include_right = include
        bad_bound = include_left and math.isinf(left)
        bad_bound = bad_bound or include_right and math.isinf(right)
        if bad_bound:
            raise ValueError('infinity cannot be included')

        self.left, self.right, self.include = left, right, include

    def __hash__(self):
        return hash((self.left, self.right, self.include))

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __contains__(self, value):
        if not math.isinf(value) and not math.isnan(value):
            include_left, include_right = self.include
            included = self.left < value < self.right
            included = included or include_left and value == self.left
            included = included or include_right and value == self.right
            return included

    def __str__(self):
        include_left, include_right = self.include
        left_bracket = '[' if include_left else '('
        right_bracket = ']' if include_right else ')'
        return '{}{}, {}{}'.format(left_bracket, self.left,
                                   self.right, right_bracket)

    def contains(self, column):  # Used instead of __contains__
        include_left, include_right = self.include
        included = and_(self.left < column, column < self.right)
        if include_left:
            included = or_(included, self.left == column)
        if include_right:
            included = or_(included, self.right == column)
        return included

    __repr__ = __str__


class Node:
    def __init__(self, variable, *values):
        self.variable, self.values = variable, values
        self.children, self.parents = [], []

    def __call__(self, instances, cls, *features):
        ...

        # for parent in self.parents:
        #     print(parent.variable)

    def feed(self, other):
        self.children.append(other)
        other.parents.append(self)


def execute():
    engine, session = database.initialize('sqlite:///../data/isrid-master.db')

    ages = [Interval(n, n + 10, (True, False)) for n in range(0, 100, 10)]
    age = Node(Subject.age, *ages)
    sex = Node(Subject.sex, *Subject.SEX_CODES.keys())
    weights = [Interval(n, n + 10, (True, False)) for n in range(0, 180, 10)]
    weight = Node(Subject.weight, *weights)
    heights = [Interval(n, n + 10, (True, False)) for n in range(0, 210, 10)]
    height = Node(Subject.height, *heights)
    survived = Node(Subject.survived, True, False)

    age.feed(survived)
    age.feed(weight)
    age.feed(height)
    sex.feed(survived)
    sex.feed(weight)
    sex.feed(height)
    weight.feed(survived)
    height.feed(survived)

    instances = session.query(Subject)

    P = survived
    print('Probability of survival (naive):',
          P(instances, Subject.survived == True))

    database.terminate(engine, session)


if __name__ == '__main__':
    execute()
