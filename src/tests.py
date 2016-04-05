#!/usr/bin/env python3

"""
tests
=====
Unit Testing
"""

import unittest
import warnings

import database
from database.cleaning import extract_numbers
from database.models import Subject, Group, Point, Location, Weather
from database.models import Operation, Outcome, Search, Incident


class ModelTests(unittest.TestCase):
    def setUp(self):
        self.engine, self.session = database.initialize('sqlite:///:memory:')

        self.group = Group()
        self.subject = Subject(sex='female', weight=25, height=100,
                               group=self.group)

        self.location = Location()
        self.weather = Weather()

        self.operation = Operation()
        self.outcome = Outcome()
        self.search = Search()

        self.incident = Incident(source='US-CAm', group=self.group,
                                 location=self.location, weather=self.weather,
                                 operation=self.operation,
                                 outcome=self.outcome, search=self.search)

        new_models = [self.group, self.subject, self.location, self.weather,
                      self.operation, self.outcome, self.search, self.incident]
        for new_model in new_models:
            self.session.add(new_model)

        self.session.commit()

    def test_validation(self):
        with self.assertRaises(ValueError):
            subject = Subject(age=-1)

        with self.assertRaises(ValueError):
            subject = Subject(height=-0.01)

        with self.assertRaises(ValueError):
            self.subject.weight = -1

        self.subject.sex = 'male'  # Should be ok with reverse lookup
        with self.assertRaises(ValueError):
            self.subject.sex = 'invalid'

        point = Point(latitude=90, longitude=-180)

        with self.assertRaises(ValueError):
            point.latitude = -90.1

        with self.assertRaises(ValueError):
            point.longitude = 180.1

        with self.assertRaises(ValueError):
            self.weather.low_temp, self.weather.high_temp = 10, -10

    def test_back_population(self):
        self.assertEqual(self.incident.group, self.group)
        self.assertEqual(self.incident, self.group.incident)
        self.assertTrue(self.subject in self.group.subjects)
        self.assertEqual(self.group, self.subject.group)

        self.assertEqual(self.incident.location, self.location)
        self.assertEqual(self.incident, self.location.incident)
        self.assertEqual(self.incident.weather, self.weather)
        self.assertEqual(self.incident, self.weather.incident)

        self.assertEqual(self.incident.operation, self.operation)
        self.assertEqual(self.incident, self.operation.incident)
        self.assertEqual(self.incident.outcome, self.outcome)
        self.assertEqual(self.incident, self.outcome.incident)
        self.assertEqual(self.incident.search, self.search)
        self.assertEqual(self.incident, self.search.incident)

    def test_querying(self):
        query = self.session.query(Subject)
        self.assertEqual(query.count(), 1)

        self.subject.age = 20
        self.session.commit()
        query = self.session.query(Subject).filter(Subject.age > 20)
        self.assertEqual(query.count(), 0)

    def test_properties(self):
        self.assertEqual(self.subject.sex_as_str, 'female')
        self.assertEqual(self.subject.bmi, 25)
        self.assertEqual(self.subject.dead_on_arrival, None)
        self.subject.status = 'DOA'
        self.assertTrue(self.subject.dead_on_arrival)
        self.assertFalse(self.subject.survived)

        self.assertEqual(self.group.size, 1)

        self.assertEqual(self.location.region, 'CA')
        self.assertEqual(self.location.country, 'US')

        self.weather.low_temp, self.weather.high_temp = -5, 10
        self.assertEqual(self.weather.avg_temp, 2.5)
        # HDD and CDD are mutually exclusive
        self.assertEqual(self.weather.hdd, 15.5)
        self.assertEqual(self.weather.cdd, None)

    def tearDown(self):
        database.terminate(self.engine, self.session)


class CleaningTests(unittest.TestCase):
    def test_extract_number(self):
        self.assertEqual(list(extract_numbers('2 people')), [2])
        self.assertEqual(list(extract_numbers('1, 2.2, 3., -.4')),
                         [1, 2.2, 3, -0.4])
        self.assertEqual(list(extract_numbers('no numbers')), [])


class DatabaseIntegrityTests(unittest.TestCase):
    def setUp(self):
        url = 'sqlite:///../data/isrid-master.db'
        self.engine, self.session = database.initialize(url)

    def test_unique_cases(self):
        columns = Incident.key, Incident.mission, Incident.number
        criteria = map(lambda column: column != None, columns)

        query = self.session.query(*columns).filter(*criteria)
        identifiers = list(map(frozenset, query))
        self.assertEqual(len(identifiers), len(set(identifiers)))

    def tearDown(self):
        database.terminate(self.engine, self.session)


if __name__ == '__main__':
    unittest.main()
