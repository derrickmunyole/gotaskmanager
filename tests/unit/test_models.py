import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base, User


@pytest.fixture(scope="function")
def db_session():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    User.__table__.create(engine, checkfirst=True)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_new_user(db_session):
    user = User(first_name='Pat', last_name='Kennedy', username='patkennedy79', email='patkennedy79@gmail.com')
    user.set_password('FlaskIsAwesome')
    db_session.add(user)
    db_session.commit()

    assert user.first_name == 'Pat'
    assert user.last_name == 'Kennedy'
    assert user.username == 'patkennedy79'
    assert user.email == 'patkennedy79@gmail.com'
    assert user.password_hash != 'FlaskIsAwesome'
    assert user.check_password('FlaskIsAwesome')
    assert not user.check_password('WrongPassword')
