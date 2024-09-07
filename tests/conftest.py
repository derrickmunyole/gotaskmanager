import pytest
from sqlalchemy import inspect
from app import create_app, db
from config import TestConfig


@pytest.fixture(scope='module')
def app():
    app = create_app(TestConfig)
    print(f"Test database URL: {app.config['SQLALCHEMY_DATABASE_URI']}")
    return app


@pytest.fixture(scope='module')
def test_client(app):
    app = create_app()
    with app.test_client() as client:
        yield client


@pytest.fixture(scope='function')
def init_database(app):
    with app.app_context():
        db.drop_all()  # Drop all tables
        db.create_all()  # Create all tables

        # Use inspect to get table names
        inspector = inspect(db.engine)
        table_names = inspector.get_table_names()
        print("Tables after creation:", table_names)

    yield  # This provides the database to the test

    with app.app_context():
        db.session.remove()
        db.drop_all()  # Clean up after the test

        # Use inspect again to verify table deletion
        inspector = inspect(db.engine)
        table_names = inspector.get_table_names()
        print("Tables after deletion:", table_names)
