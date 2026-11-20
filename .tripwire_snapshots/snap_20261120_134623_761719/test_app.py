import unittest
from app import login

class TestLoginFunction(unittest.TestCase):
    def test_valid_login_alice(self):
        """Alice should be able to log in with her correct password."""
        self.assertTrue(
            login("alice", "correct_horse_battery_staple"),
            "Valid credentials for alice must return True"
        )

    def test_valid_login_bob(self):
        """Bob should be able to log in with his correct password."""
        self.assertTrue(
            login("bob", "super_secret_p@ss123"),
            "Valid credentials for bob must return True"
        )

    def test_invalid_password(self):
        """Supplying an incorrect password must be rejected."""
        self.assertFalse(
            login("alice", "wrong_password_attempt"),
            "Invalid password must return False"
        )

    def test_unknown_user(self):
        """An unknown user must be rejected."""
        self.assertFalse(
            login("unknown_user", "any_password"),
            "Non-existent user must return False"
        )

    def test_empty_credentials(self):
        """Empty username or password must be rejected."""
        self.assertFalse(login("", "pass"))
        self.assertFalse(login("alice", ""))

if __name__ == "__main__":
    unittest.main()

