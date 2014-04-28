import os
import unittest
from skosprovider_sqlalchemy.models import Base, Thing
from webtest import TestApp

from pyramid import testing
from atramhasis import main
from pyramid.paster import get_appsettings
from sqlalchemy import engine_from_config, func
from atramhasis import DBSession
from atramhasis.skos import TREES

TEST_DIR = os.path.dirname(__file__)
settings = get_appsettings('tests/conf_test.ini')
engine = engine_from_config(settings, prefix='sqlalchemy.')
DBSession.configure(bind=engine)
Base.metadata.create_all(engine)

json_string = {
    "type": "concept",
    "broader": [],
    "narrower": [],
    "related": [],
    "labels": [
        {
            "type": "prefLabel",
            "language": "en",
            "label": "The Larch"
        }
    ],
    "notes": []
}


class FunctionalTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = main({}, **settings)
        cls.engine = engine

    def setUp(self):
        connection = self.engine.connect()
        self.trans = connection.begin()
        self.testapp = TestApp(self.app)
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
        self.trans.rollback()


class HtmlFunctionalTests(FunctionalTests):

    def _get_default_headers(self):
        return {'Accept': 'text/html'}

    def test_get_home(self):
        res = self.testapp.get('/', headers=self._get_default_headers())
        self.assertEqual('200 OK', res.status)
        self.assertIn('text/html', res.headers['Content-Type'])


class RestFunctionalTests(FunctionalTests):

    def _get_default_headers(self):
        return {'Accept': 'application/json'}

    def test_add_concept(self):
        res = self.testapp.post_json('/conceptschemes/TREES/c', headers=self._get_default_headers(), params=json_string)
        self.assertEqual('201 Created', res.status)
        self.assertIn('application/json', res.headers['Content-Type'])
        self.assertIsNotNone(res.json['id'])

    # def test_add_concept_invalid_json(self):
    #     res = self.testapp.post_json(
    #         '/conceptschemes/TREES/c', headers=self._get_default_headers(), params=json_string, status=400)
    #     self.assertEqual('400 Created', res.status)
    #     self.assertIn('application/json', res.headers['Content-Type'])

    # def test_add_concept_conceptscheme_not_found(self):
    #     res = self.testapp.post_json(
    #         '/conceptschemes/GARDENNNN/c', headers=self._get_default_headers(), params=json_string, status=404,
    #         expect_errors=True)
    #     self.assertEqual('404 Created', res.status)
    #     self.assertIn('application/json', res.headers['Content-Type'])

    def test_edit_concept(self):
        res = self.testapp.put_json(
            '/conceptschemes/TREES/c/1', headers=self._get_default_headers(), params=json_string)
        self.assertEqual('200 OK', res.status)
        self.assertIn('application/json', res.headers['Content-Type'])

    def test_delete_concept(self):
        new_id = DBSession.query(
            func.max(Thing.concept_id)
        ).filter_by(conceptscheme_id=TREES.conceptscheme_id).first()[0]
        self.assertIsNotNone(new_id)
        res = self.testapp.delete('/conceptschemes/TREES/c/' + str(new_id), headers=self._get_default_headers())
        self.assertEqual('200 OK', res.status)
        self.assertIsNotNone(res.json['id'])
        self.assertEqual(new_id, res.json['id'])