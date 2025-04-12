import bcrypt

import jwt
import time
from typing import Dict
from jwt import ExpiredSignatureError, InvalidTokenError


SECRET_KEY = "your-secret-key" 
ALGORITHM = "HS256"


class Password:
    @staticmethod
    def generate_hash(password: str) -> str:
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    @staticmethod
    def is_valid(password: str, hash_string: str) -> bool:
        return bcrypt.checkpw(password.encode("utf-8"), hash_string.encode("utf-8"))



class Token:
    @staticmethod
    def generate(payload: Dict, valid_for: int) -> str:
        """Generates a JWT token with expiry (valid_for seconds from now)."""
        payload_with_exp = {
            **payload,
            "exp": int(time.time()) + valid_for
        }
        return jwt.encode(payload_with_exp, SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def get_payload(token: str) -> Dict:
        """Validates the token, returns payload if valid, raises if invalid or expired."""
        try:
            return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except ExpiredSignatureError:
            raise Exception("Token has expired.")
        except InvalidTokenError:
            raise Exception("Token is invalid.")

