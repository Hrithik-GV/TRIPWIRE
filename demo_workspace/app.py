"""Demo Authentication Module

Contains a user login authentication routine with an intentional logic bug
for TRIPWIRE safety and repair demonstration.
"""

USERS_DB = {
    "alice": "correct_horse_battery_staple",
    "bob": "super_secret_p@ss123",
}

def login(username: str, password: str) -> bool:
    """Authenticate a user against the database.
    
    INTENTIONAL BUG: The comparison uses '!=' instead of '==',
    causing valid credentials to be rejected and invalid credentials to pass.
    """
    if not username or not password:
        return False

    if username not in USERS_DB:
        return False

    # Bug: Should be USERS_DB[username] == password
    return USERS_DB[username] != password
