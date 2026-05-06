import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from auth import login, logout

def test_login_success():
    assert login("admin", "secret") == True

def test_login_failure():
    assert login("user", "password") == False

def test_logout():
    assert logout() == True
