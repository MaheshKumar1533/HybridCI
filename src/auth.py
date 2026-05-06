def login(username, password):
    if username == "admin" and password == "secret":
        return True
    return False

def logout():
    return True
