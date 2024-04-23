import pytest
from flask_testing import TestCase
from search_engine import create_app, db
from search_engine.models import User

class MyTest(TestCase):

    def create_app(self):
        return create_app('search_engine.config.TestingConfig')

    def setUp(self):
        db.create_all()
        user = User(username='testuser', email='test@example.com')
        user.set_password('testpassword')
        db.session.add(user)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_user_creation(self):
        user = User.query.filter_by(username='testuser').first()
        assert user is not None

    def test_user_password(self):
        user = User.query.filter_by(username='testuser').first()
        assert user.check_password('testpassword') is True
        assert user.check_password('wrongpassword') is False
