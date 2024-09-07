# tests/test_config.py

def test_testing_config(app):
    assert app.config['TESTING'] == True
    assert app.config['SQLALCHEMY_DATABASE_URI'] == 'postgresql://localhost:5432/gotaskmanager_test'
