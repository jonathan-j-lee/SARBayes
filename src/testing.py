#!/usr/bin/env python3

"""
testing
"""

import unittest

from sqlalchemy.exc import IntegrityError

import database
from database.models import Subject, Group, Incident


class ModelTests(unittest.TestCase):
    def setUp(self):
        self.engine, self.session = database.initialize()
        self.incident = Incident()
        self.group = Group(incident=self.incident)
        self.subjects = [Subject(group=self.group) for index in range(10)]

        self.session.add(self.incident)
        self.session.add(self.group)
        for subject in self.subjects:
            self.session.add(subject)
        self.session.commit()

    def _test_invalid_values(self):
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

        self.assertEqual(self.group.size, len(self.subjects))

    def tearDown(self):
        database.terminate(self.engine, self.session)


if __name__ == '__main__':
    unittest.main()
