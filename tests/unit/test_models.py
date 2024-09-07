import pytest
from app.models import User


def test_new_user():
    """
    GIVEN a User model
    WHEN a new User is created
    THEN check the email, username, hashed_password, and password verification work correctly
    """
    user = User(first_name='Pat', last_name='Kennedy', username='patkennedy79', email='patkennedy79@gmail.com')
    user.set_password('FlaskIsAwesome')

    assert user.first_name == 'Pat'
    assert user.last_name == 'Kennedy'
    assert user.full_name == 'Pat Kennedy'
    assert user.username == 'patkennedy79'
    assert user.email == 'patkennedy79@gmail.com'
    assert user.password_hash != 'FlaskIsAwesome'
    assert user.check_password('FlaskIsAwesome')
    assert not user.check_password('WrongPassword')

