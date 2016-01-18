#!/usr/bin/env python3

"""
testing
"""

import unittest

from sqlalchemy.exc import IntegrityError

import database
from database.models import Subject, Group, Incident, Location


class ModelTests(unittest.TestCase):
    def setUp(self):
        self.engine, self.session = database.initialize()
        self.incident = Incident(source='US-CAm')
        self.group = Group(incident=self.incident)
        self.subjects = [Subject(group=self.group) for index in range(10)]
        self.location = Location(incident=self.incident)

        self.session.add(self.incident)
        self.session.add(self.group)
        for subject in self.subjects:
            self.session.add(subject)
        self.session.add(self.location)
        self.session.commit()

    def _test_validation(self):
        with self.assertRaises(ValueError):
            subject = Subject(age=-1)
        with self.assertRaises(ValueError):
            subject = Subject(height=0)

    def test_back_population(self):
        self.assertEqual(self.incident.group, self.group)
        self.assertEqual(self.incident, self.group.incident)

        for subject in self.subjects:
            self.assertTrue(subject in self.group.subjects)
            self.assertEqual(subject.group, self.group)

        self.assertEqual(self.incident.location, self.location)
        self.assertEqual(self.location, self.incident.location)

    def test_properties(self):
        self.assertEqual(self.group.size, len(self.subjects))
        self.assertEqual(self.location.region, 'CA')
        self.assertEqual(self.location.country, 'US')

    def tearDown(self):
        database.terminate(self.engine, self.session)


if __name__ == '__main__':
    unittest.main()
