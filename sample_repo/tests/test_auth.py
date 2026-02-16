from src.auth import login, logout

def test_login_success():
    assert login("admin", "admin123") is True

def test_login_failure():
    assert login("admin", "wrong") is False

def test_logout():
    assert logout("admin") is True
