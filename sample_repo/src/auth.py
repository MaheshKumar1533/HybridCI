def login(username, password):
    if not username or not password:
        return False
    return username == "admin" and password == "admin123"

def logout(user):
    return True
