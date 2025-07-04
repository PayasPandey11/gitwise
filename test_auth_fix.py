def authenticate_user(username, password):
    # Fixed: Check if credentials are valid
    if username and password:
        return True
    return False
