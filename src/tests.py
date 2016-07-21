#!/usr/bin/env python3

"""
tests
=====
Unit Testing
"""

import hashlib
import os
import random
import unittest
import warnings
import yaml

import database
from database.cleaning import extract_numbers
from database.models import Subject, Group, Incident, Location, Point
from database.models import Operation, Outcome, Weather, Search
from database.processing import survival_rate, tabulate
from evaluation import compute_brier_score
from weather import noaa, wsi


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

        instances = [self.group, self.subject, self.location, self.weather,
                  self.operation, self.outcome, self.search, self.incident]
        for instance in instances:
            self.session.add(instance)

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

    def test_properties(self):
        self.assertEqual(self.subject.sex_as_str, 'female')
        self.assertEqual(self.subject.bmi, 25)
        self.assertEqual(self.subject.dead_on_arrival, None)

        self.subject.status = 'DOA'
        self.session.commit()
        self.assertTrue(self.subject.dead_on_arrival)
        self.assertFalse(self.subject.survived)

        self.assertEqual(self.group.size, 1)

        self.assertEqual(self.location.region, 'CA')
        self.assertEqual(self.location.country, 'US')

        self.weather.low_temp, self.weather.high_temp = -5, 10
        self.session.commit()
        self.assertAlmostEqual(self.weather.avg_temp, 2.5)
        # HDD and CDD are mutually exclusive
        self.assertAlmostEqual(self.weather.hdd, 15.5)
        self.assertEqual(self.weather.cdd, None)

    def tearDown(self):
        database.terminate(self.engine, self.session)


class QueryingTests(unittest.TestCase):
    def setUp(self):
        self.engine, self.session = database.initialize('sqlite:///:memory:')

        for age in range(1, 11):
            status = 'DOA' if random.random() < 0.5 else 'Well'
            subject = Subject(age=age, status=status)
            if age < 6:
                subject.weight = 20
            self.session.add(subject)

        self.session.commit()

    def test_retrieval(self):
        models = Subject, Group, Incident, Location, Point
        models += Operation, Outcome, Weather, Search

        for model in models:
            instances = self.session.query(model).all()
            for instance in instances:
                self.assertTrue(isinstance(instance, model))

    def test_count(self):
        results = self.session.query(Subject)
        self.assertEqual(results.count(), 10)

        results = self.session.query(Subject).filter(Subject.age < 5)
        self.assertEqual(results.count(), 4)

        results = self.session.query(Subject).filter(Subject.sex != None)
        self.assertEqual(results.count(), 0)

    def test_column_properties(self):
        query = self.session.query(Subject)
        self.assertEqual(query.filter(Subject.dead_on_arrival == None).count(),
                         query.filter(Subject.survived == None).count())
        self.assertEqual(query.filter(Subject.dead_on_arrival).count(),
                         query.filter(Subject.survived == False).count())
        self.assertEqual(query.filter(Subject.survived).count(), query.filter(
                         Subject.dead_on_arrival == False).count())

    def test_tabulation(self):
        query = self.session.query(Subject.survived, Subject.age)
        df = tabulate(query)

        self.assertEqual(list(df.columns), ['survived', 'age'])
        self.assertEqual(len(df), self.session.query(Subject).count())
        for columns in df.itertuples(False):
            for value in columns:
                self.assertIsNotNone(value)

    def tearDown(self):
        database.terminate(self.engine, self.session)


class DeletionTests(unittest.TestCase):
    def setUp(self):
        self.engine, self.session = database.initialize('sqlite:///:memory:')

        self.subjects = [Subject() for number in range(10)]
        self.ipp = Point(latitude=0, longitude=0)
        self.group = Group(subjects=self.subjects)
        self.operation = Operation(ipp=self.ipp)
        self.incident = Incident(group=self.group, operation=self.operation)

        instances = [self.ipp, self.group, self.operation, self.incident]
        for instance in self.subjects + instances:
            self.session.add(instance)
        self.session.commit()

    def test_cascade(self):
        query = self.session.query(Incident)
        self.assertEqual(query.count(), 1)

        self.session.delete(query.first())
        self.session.commit()
        self.assertEqual(query.count(), 0)

        self.assertEqual(Subject.query.count(), 0)
        self.assertEqual(Point.query.count(), 0)
        self.assertEqual(Group.query.count(), 0)
        self.assertEqual(Operation.query.count(), 0)

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

    def test_checksums(self):
        self.assertTrue(os.path.exists('../data/checksums.txt'))

        with open('../data/checksums.txt') as checksums_file:
            checksums = checksums_file.read().strip().split('\n')

        for checksum in checksums:
            checksum, filename = checksum[:32], checksum[34:].split('/')[-1]

            if filename != 'checksums.txt':
                hashing = hashlib.md5()
                filename = os.path.join('../data/', filename)

                with open(filename, 'rb') as data_file:
                    for chunk in iter(lambda: data_file.read(4096), b''):
                        hashing.update(chunk)

                self.assertEqual(hashing.hexdigest(), checksum)

    def tearDown(self):
        database.terminate(self.engine, self.session)


class EvaluationTests(unittest.TestCase):
    def test_brier_score(self):
        self.assertAlmostEqual(compute_brier_score([1, 0], [0.5, 0.5]), 0.25)


class WeatherFetchingTests(unittest.TestCase):
    def setUp(self):
        with open('../data/config.yaml') as config_file:
            self.config = yaml.load(config_file.read())

        wsi.DEFAULT_PARAMETERS['userKey'] = self.config['wsi']['key']
        noaa.API_TOKEN = self.config['noaa']['key']

    def test_connectivity(self):
        ...


if __name__ == '__main__':
    unittest.main()
